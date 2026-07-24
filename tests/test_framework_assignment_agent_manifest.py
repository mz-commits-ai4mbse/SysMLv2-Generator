"""Tests for the persona-local Framework Assignment Agent Result."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import json

import pytest

from modules.framework_assignment.agent_manifest import (
    FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION,
    create_framework_assignment_agent_candidate,
    create_framework_assignment_agent_result,
    create_framework_assignment_basis,
    create_framework_assignment_proposal,
    framework_assignment_agent_result_from_json,
    framework_assignment_agent_result_to_dict,
    framework_assignment_agent_result_to_json,
    parse_framework_assignment_agent_result,
    validate_framework_assignment_agent_result,
)
from modules.framework_assignment.errors import (
    DuplicateFrameworkAssignmentAgentCandidateError,
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentAgentCandidate,
    FrameworkAssignmentAgentResult,
)
from modules.information_units.types import InformationUnit


PROJECT_ID = "318604"
INFORMATION_UNIT_ID = "IU-000001"
FINGERPRINT = "a" * 64
TIMESTAMP = "2026-07-24T18:00:00Z"


def information_unit(
    *,
    content_fingerprint: str = FINGERPRINT,
) -> InformationUnit:
    value = object.__new__(InformationUnit)
    bindings = {
        "project_id": PROJECT_ID,
        "source_id": "SRC-000001",
        "source_projection_id": "SP-000001",
        "information_unit_id": INFORMATION_UNIT_ID,
        "content_fingerprint": content_fingerprint,
    }
    for name, field_value in bindings.items():
        object.__setattr__(value, name, field_value)
    return value


def information_basis(
    *,
    reference_id: str = INFORMATION_UNIT_ID,
    reference_version: str | None = FINGERPRINT,
) -> object:
    return create_framework_assignment_basis(
        basis_type="information_unit",
        reference_id=reference_id,
        reference_version=reference_version,
        rationale="The assignment classifies this exact claim.",
    )


def terminology_basis(
    *,
    reference_id: str = "TMC-000001",
    reference_version: str | None = "b" * 64,
) -> object:
    return create_framework_assignment_basis(
        basis_type="terminology_mapping_candidate",
        reference_id=reference_id,
        reference_version=reference_version,
        rationale="Terminology supports the framework meaning.",
    )


def turing_basis(
    *,
    reference_id: str = "TC-000001",
    reference_version: str | None = "1.0.0",
) -> object:
    return create_framework_assignment_basis(
        basis_type="turing_core_concept",
        reference_id=reference_id,
        reference_version=reference_version,
        rationale="Turing Core supports the framework meaning.",
    )


def semantic_basis() -> object:
    return create_framework_assignment_basis(
        basis_type="semantic_interpretation",
        reference_id=(
            "IU-000001/interpreted_statement"
        ),
        reference_version=None,
        rationale="Statement semantics support the assignment.",
    )


def proposal(
    *,
    framework_node_id: str = "FW_SYSTEM_REQUIREMENTS",
    bases: tuple[object, ...] | None = None,
) -> object:
    return create_framework_assignment_proposal(
        framework_node_id=framework_node_id,
        assignment_bases=(
            (information_basis(),)
            if bases is None
            else bases
        ),
        rationale="The claim expresses a system requirement.",
    )


def agent_candidate(
    *,
    candidate_id: str = "FAAC-000001",
    information_unit_id: str = INFORMATION_UNIT_ID,
    status: str = "assigned",
    proposals: tuple[object, ...] | None = None,
) -> FrameworkAssignmentAgentCandidate:
    return create_framework_assignment_agent_candidate(
        framework_assignment_agent_candidate_id=candidate_id,
        information_unit_id=information_unit_id,
        assignment_status=status,
        proposals=(
            (proposal(),)
            if proposals is None
            else proposals
        ),
        rationale="Persona-local classification.",
        uncertainties=(),
    )


def agent_result(
    *,
    unit: InformationUnit | None = None,
    candidates: tuple[FrameworkAssignmentAgentCandidate, ...]
    | None = None,
    no_candidate_rationale: str | None = None,
    terminology_ids: tuple[str, ...] = ("TMC-000001",),
) -> FrameworkAssignmentAgentResult:
    selected_unit = information_unit() if unit is None else unit
    selected_candidates = (
        (agent_candidate(),)
        if candidates is None
        else candidates
    )
    return create_framework_assignment_agent_result(
        information_unit=selected_unit,
        team_id="framework-team",
        agent_id="agent-a",
        persona_id="persona-a",
        persona_run_index=1,
        persona_configuration_fingerprint="c" * 64,
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=terminology_ids,
        candidates=selected_candidates,
        no_candidate_rationale=no_candidate_rationale,
        timestamp=TIMESTAMP,
    )


def payload() -> dict[str, object]:
    return framework_assignment_agent_result_to_dict(
        agent_result()
    )


def test_schema_version_is_explicit() -> None:
    assert FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION == (
        "1.0.0"
    )


def test_creates_valid_result() -> None:
    result = agent_result()

    assert result.project_id == PROJECT_ID
    assert result.information_unit_id == INFORMATION_UNIT_ID
    assert result.framework_template_id == (
        "TURING_RFLP_FRAMEWORK"
    )
    assert result.framework_template_version == "1.0.0"
    assert len(result.candidates) == 1


def test_all_manifest_types_are_frozen_and_slotted() -> None:
    result = agent_result()
    values = (
        result,
        result.candidates[0],
        result.candidates[0].proposals[0],
        result.candidates[0].proposals[0].assignment_bases[0],
    )

    for value in values:
        assert value.__dataclass_params__.frozen
        assert value.__slots__
    with pytest.raises(FrozenInstanceError):
        result.team_id = "other"


def test_agent_result_has_no_consensus_or_approval_fields() -> None:
    result_fields = {
        field.name
        for field in fields(FrameworkAssignmentAgentResult)
    }
    candidate_fields = {
        field.name
        for field in fields(FrameworkAssignmentAgentCandidate)
    }
    forbidden = {
        "confidence",
        "consensus_level",
        "variance_level",
        "confirmation_required",
        "review_required",
        "approved",
        "accepted",
    }

    assert forbidden.isdisjoint(result_fields)
    assert forbidden.isdisjoint(candidate_fields)


def test_deterministic_json_round_trip() -> None:
    result = agent_result()
    first = framework_assignment_agent_result_to_json(result)
    reloaded = framework_assignment_agent_result_from_json(first)
    second = framework_assignment_agent_result_to_json(reloaded)

    assert reloaded == result
    assert first == second
    assert first.endswith("\n")


def test_dictionary_round_trip() -> None:
    result = agent_result()

    assert parse_framework_assignment_agent_result(
        framework_assignment_agent_result_to_dict(result)
    ) == result
    validate_framework_assignment_agent_result(result)


def test_multiple_assigned_nodes_are_valid() -> None:
    selected = agent_candidate(
        proposals=(
            proposal(
                framework_node_id="FW_SYSTEM_REQUIREMENTS"
            ),
            proposal(
                framework_node_id="FW_SYSTEM_FUNCTIONAL"
            ),
        )
    )
    result = agent_result(candidates=(selected,))

    assert result.candidates[0].assignment_status == "assigned"
    assert len(result.candidates[0].proposals) == 2


@pytest.mark.parametrize(
    "status",
    (
        "ambiguous",
        "conflict",
    ),
)
def test_ambiguous_and_conflict_require_multiple_nodes(
    status: str,
) -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_candidate(status=status)

    selected = agent_candidate(
        status=status,
        proposals=(
            proposal(
                framework_node_id="FW_SYSTEM_REQUIREMENTS"
            ),
            proposal(
                framework_node_id="FW_STAKEHOLDER_REQUIREMENTS"
            ),
        ),
    )
    assert selected.assignment_status == status


def test_unassigned_candidate_has_no_proposals() -> None:
    selected = agent_candidate(
        status="unassigned",
        proposals=(),
    )

    assert selected.proposals == ()


def test_unassigned_candidate_rejects_proposals() -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_candidate(status="unassigned")


def test_assigned_candidate_requires_proposal() -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_candidate(status="assigned", proposals=())


def test_duplicate_framework_nodes_are_rejected() -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_candidate(
            proposals=(proposal(), proposal())
        )


def test_every_proposal_requires_information_unit_basis() -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        proposal(bases=(semantic_basis(),))


def test_evidence_bases_may_be_combined() -> None:
    selected = proposal(
        bases=(
            information_basis(),
            terminology_basis(),
            turing_basis(),
            semantic_basis(),
        )
    )

    assert {
        basis.basis_type
        for basis in selected.assignment_bases
    } == {
        "information_unit",
        "terminology_mapping_candidate",
        "turing_core_concept",
        "semantic_interpretation",
    }


@pytest.mark.parametrize(
    ("basis_type", "reference_id", "reference_version"),
    (
        ("information_unit", "wrong", FINGERPRINT),
        ("information_unit", INFORMATION_UNIT_ID, None),
        (
            "terminology_mapping_candidate",
            "wrong",
            "b" * 64,
        ),
        (
            "terminology_mapping_candidate",
            "TMC-000001",
            "1.0.0",
        ),
        ("turing_core_concept", "wrong", "1.0.0"),
        ("turing_core_concept", "TC-000001", None),
        (
            "semantic_interpretation",
            "IU-000001/statement",
            "1.0.0",
        ),
    ),
)
def test_invalid_basis_contracts_are_rejected(
    basis_type: str,
    reference_id: str,
    reference_version: str | None,
) -> None:
    with pytest.raises(
        (
            FrameworkAssignmentValidationError,
            FrameworkAssignmentIntegrityError,
        )
    ):
        create_framework_assignment_basis(
            basis_type=basis_type,
            reference_id=reference_id,
            reference_version=reference_version,
            rationale="Test.",
        )


def test_information_unit_basis_binds_exact_fingerprint() -> None:
    changed_unit = information_unit(
        content_fingerprint="d" * 64
    )

    with pytest.raises(FrameworkAssignmentReferenceError):
        agent_result(unit=changed_unit)


def test_terminology_basis_must_be_declared_by_result() -> None:
    selected = agent_candidate(
        proposals=(
            proposal(
                bases=(
                    information_basis(),
                    terminology_basis(
                        reference_id="TMC-000002"
                    ),
                )
            ),
        )
    )

    with pytest.raises(FrameworkAssignmentReferenceError):
        agent_result(candidates=(selected,))


def test_turing_basis_version_must_match_result() -> None:
    selected = agent_candidate(
        proposals=(
            proposal(
                bases=(
                    information_basis(),
                    turing_basis(reference_version="2.0.0"),
                )
            ),
        )
    )

    with pytest.raises(FrameworkAssignmentReferenceError):
        agent_result(candidates=(selected,))


def test_candidate_must_reference_result_information_unit() -> None:
    with pytest.raises(FrameworkAssignmentReferenceError):
        agent_result(
            candidates=(
                agent_candidate(
                    information_unit_id="IU-000002"
                ),
            )
        )


def test_result_may_record_no_candidate() -> None:
    result = agent_result(
        candidates=(),
        no_candidate_rationale=(
            "The persona found no defensible assignment."
        ),
        terminology_ids=(),
    )

    assert result.candidates == ()
    assert result.no_candidate_rationale is not None


@pytest.mark.parametrize(
    ("candidates", "rationale"),
    (
        ((), None),
        (
            (agent_candidate(),),
            "Contradictory no-candidate rationale.",
        ),
    ),
)
def test_candidate_and_no_candidate_are_exclusive(
    candidates: tuple[FrameworkAssignmentAgentCandidate, ...],
    rationale: str | None,
) -> None:
    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_result(
            candidates=candidates,
            no_candidate_rationale=rationale,
        )


def test_more_than_one_candidate_is_rejected() -> None:
    second = agent_candidate(candidate_id="FAAC-000002")

    with pytest.raises(FrameworkAssignmentIntegrityError):
        agent_result(
            candidates=(agent_candidate(), second)
        )


def test_duplicate_candidate_ids_are_rejected_first() -> None:
    first = agent_candidate()
    second = replace(
        first,
        proposals=(
            proposal(
                framework_node_id="FW_SYSTEM_FUNCTIONAL"
            ),
        ),
    )
    data = payload()
    candidate_data = deepcopy(data["candidates"][0])
    second_data = deepcopy(candidate_data)
    second_data["proposals"] = [
        framework_assignment_agent_result_to_dict(
            agent_result(candidates=(second,))
        )["candidates"][0]["proposals"][0]
    ]
    data["candidates"] = [candidate_data, second_data]

    with pytest.raises(
        DuplicateFrameworkAssignmentAgentCandidateError
    ):
        parse_framework_assignment_agent_result(data)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("schema_version", "2.0.0"),
        ("project_id", ""),
        ("source_id", " source"),
        ("source_projection_id", []),
        ("information_unit_id", "IU-00001"),
        ("team_id", "team id"),
        ("agent_id", ""),
        ("persona_id", None),
        ("persona_run_index", 0),
        ("persona_run_index", True),
        ("persona_configuration_fingerprint", "a"),
        ("llm_provider", " test"),
        ("llm_model", ""),
        ("prompt_schema_version", "1.0"),
        ("framework_template_id", "lowercase"),
        ("framework_template_version", "v1"),
        ("turing_core_version", "1"),
        ("project_glossary_revision", 0),
        ("terminology_mapping_candidate_ids", "TMC-000001"),
        ("candidates", {}),
        ("created_at", "2026-07-24"),
    ),
)
def test_invalid_top_level_values_are_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    data = payload()
    data[field_name] = invalid_value

    with pytest.raises(
        (
            FrameworkAssignmentValidationError,
            FrameworkAssignmentIntegrityError,
        )
    ):
        parse_framework_assignment_agent_result(data)


@pytest.mark.parametrize(
    "expected_field",
    (
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
    ),
)
def test_expected_identifiers_are_enforced(
    expected_field: str,
) -> None:
    arguments = {
        "expected_project_id": PROJECT_ID,
        "expected_source_id": "SRC-000001",
        "expected_source_projection_id": "SP-000001",
        "expected_information_unit_id": INFORMATION_UNIT_ID,
    }
    arguments[f"expected_{expected_field}"] = "wrong"

    with pytest.raises(FrameworkAssignmentReferenceError):
        parse_framework_assignment_agent_result(
            payload(),
            **arguments,
        )


def test_unknown_top_level_field_is_rejected() -> None:
    data = payload()
    data["confidence"] = "high"

    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_agent_result(data)


def test_missing_top_level_field_is_rejected() -> None:
    data = payload()
    del data["framework_template_version"]

    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_agent_result(data)


@pytest.mark.parametrize(
    "nested_collection",
    (
        "candidates",
        "proposals",
        "assignment_bases",
    ),
)
def test_unknown_nested_fields_are_rejected(
    nested_collection: str,
) -> None:
    data = payload()
    if nested_collection == "candidates":
        target = data["candidates"][0]
    elif nested_collection == "proposals":
        target = data["candidates"][0]["proposals"][0]
    else:
        target = (
            data["candidates"][0]["proposals"][0][
                "assignment_bases"
            ][0]
        )
    target["unexpected"] = True

    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_agent_result(data)


def test_duplicate_json_keys_are_rejected() -> None:
    text = framework_assignment_agent_result_to_json(
        agent_result()
    )
    duplicated = text.replace(
        '"schema_version": "1.0.0",',
        (
            '"schema_version": "1.0.0",\n'
            '  "schema_version": "1.0.0",'
        ),
        1,
    )

    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_agent_result_from_json(duplicated)


@pytest.mark.parametrize(
    "invalid_json",
    (
        "{invalid",
        "[]",
        "null",
        "42",
    ),
)
def test_invalid_json_documents_are_rejected(
    invalid_json: str,
) -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_agent_result_from_json(
            invalid_json
        )


def test_non_string_json_input_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_agent_result_from_json(42)


def test_non_information_unit_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        agent_result(unit=object())


def test_serialization_rejects_wrong_runtime_type() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_agent_result_to_dict(object())


def test_terminology_ids_are_unique() -> None:
    data = payload()
    data["terminology_mapping_candidate_ids"] = [
        "TMC-000001",
        "TMC-000001",
    ]

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_agent_result(data)


def test_candidate_uncertainties_are_unique() -> None:
    data = payload()
    data["candidates"][0]["uncertainties"] = [
        "Boundary unclear.",
        "Boundary unclear.",
    ]

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_agent_result(data)


def test_node_reference_uses_stable_framework_id() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        proposal(framework_node_id="system.requirements")


def test_assignment_status_is_closed_vocabulary() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        agent_candidate(status="approved")


def test_result_is_json_serializable_without_custom_encoder() -> None:
    serialized = json.dumps(
        framework_assignment_agent_result_to_dict(
            agent_result()
        )
    )

    assert isinstance(serialized, str)
