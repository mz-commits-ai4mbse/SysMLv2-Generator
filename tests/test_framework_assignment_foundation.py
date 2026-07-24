"""Tests for framework-assignment errors, IDs, and immutable types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from modules.framework_assignment.errors import (
    FrameworkAssignmentAgentCandidateIdAllocationError,
    FrameworkAssignmentCandidateIdAllocationError,
    FrameworkAssignmentComparisonError,
    FrameworkAssignmentConfigurationError,
    FrameworkAssignmentError,
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentPersistenceError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from modules.framework_assignment.identifiers import (
    MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE,
    MIN_FRAMEWORK_ASSIGNMENT_SEQUENCE,
    format_framework_assignment_agent_candidate_id,
    format_framework_assignment_candidate_id,
    framework_assignment_agent_candidate_id_sequence,
    framework_assignment_candidate_id_sequence,
    is_valid_framework_assignment_agent_candidate_id,
    is_valid_framework_assignment_candidate_id,
    next_framework_assignment_agent_candidate_id,
    next_framework_assignment_candidate_id,
    validate_framework_assignment_agent_candidate_id,
    validate_framework_assignment_candidate_id,
)
from modules.framework_assignment.types import (
    FRAMEWORK_ASSIGNMENT_BASIS_TYPES,
    FRAMEWORK_ASSIGNMENT_CONFIDENCE_LEVELS,
    FRAMEWORK_ASSIGNMENT_CONSENSUS_LEVELS,
    FRAMEWORK_ASSIGNMENT_ISSUE_LEVELS,
    FRAMEWORK_ASSIGNMENT_REVIEW_MODES,
    FRAMEWORK_ASSIGNMENT_STATUSES,
    FRAMEWORK_ASSIGNMENT_VARIANCE_LEVELS,
    FrameworkAssignmentAgentCandidate,
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentAgentResult,
    FrameworkAssignmentBasis,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentIssue,
    FrameworkAssignmentProposal,
    FrameworkAssignmentScanResult,
    FrameworkAssignmentValueDistribution,
)


def test_error_hierarchy_has_one_package_root() -> None:
    errors = (
        FrameworkAssignmentValidationError,
        FrameworkAssignmentIntegrityError,
        FrameworkAssignmentConfigurationError,
        FrameworkAssignmentReferenceError,
        FrameworkAssignmentComparisonError,
        FrameworkAssignmentPersistenceError,
        FrameworkAssignmentCandidateIdAllocationError,
        FrameworkAssignmentAgentCandidateIdAllocationError,
    )

    assert all(
        issubclass(error, FrameworkAssignmentError)
        for error in errors
    )


@pytest.mark.parametrize(
    "value",
    (
        "FAAC-000001",
        "FAAC-123456",
        "FAAC-999999",
    ),
)
def test_valid_agent_candidate_ids(value: str) -> None:
    assert is_valid_framework_assignment_agent_candidate_id(
        value
    )
    assert (
        validate_framework_assignment_agent_candidate_id(value)
        == value
    )


@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        True,
        "",
        "FAAC-000000",
        "FAAC-00001",
        "FAAC-1000000",
        "FAC-000001",
        "faac-000001",
        "FAAC_000001",
        " FAAC-000001",
    ),
)
def test_invalid_agent_candidate_ids(value: object) -> None:
    assert not is_valid_framework_assignment_agent_candidate_id(
        value
    )
    with pytest.raises(FrameworkAssignmentValidationError):
        validate_framework_assignment_agent_candidate_id(value)


@pytest.mark.parametrize(
    "value",
    (
        "FAC-000001",
        "FAC-123456",
        "FAC-999999",
    ),
)
def test_valid_persistent_candidate_ids(value: str) -> None:
    assert is_valid_framework_assignment_candidate_id(value)
    assert validate_framework_assignment_candidate_id(value) == value


@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        True,
        "",
        "FAC-000000",
        "FAC-00001",
        "FAC-1000000",
        "FAAC-000001",
        "fac-000001",
        "FAC_000001",
        "FAC-000001 ",
    ),
)
def test_invalid_persistent_candidate_ids(value: object) -> None:
    assert not is_valid_framework_assignment_candidate_id(value)
    with pytest.raises(FrameworkAssignmentValidationError):
        validate_framework_assignment_candidate_id(value)


@pytest.mark.parametrize(
    ("sequence", "expected"),
    (
        (1, "FAAC-000001"),
        (42, "FAAC-000042"),
        (999_999, "FAAC-999999"),
    ),
)
def test_format_agent_candidate_id(
    sequence: int,
    expected: str,
) -> None:
    assert (
        format_framework_assignment_agent_candidate_id(sequence)
        == expected
    )


@pytest.mark.parametrize(
    ("sequence", "expected"),
    (
        (1, "FAC-000001"),
        (42, "FAC-000042"),
        (999_999, "FAC-999999"),
    ),
)
def test_format_persistent_candidate_id(
    sequence: int,
    expected: str,
) -> None:
    assert (
        format_framework_assignment_candidate_id(sequence)
        == expected
    )


@pytest.mark.parametrize(
    "sequence",
    (
        None,
        True,
        1.0,
        "1",
        0,
        -1,
        1_000_000,
    ),
)
def test_invalid_sequences_are_rejected(sequence: object) -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        format_framework_assignment_agent_candidate_id(sequence)
    with pytest.raises(FrameworkAssignmentValidationError):
        format_framework_assignment_candidate_id(sequence)


def test_identifier_sequence_readers() -> None:
    assert (
        framework_assignment_agent_candidate_id_sequence(
            "FAAC-654321"
        )
        == 654_321
    )
    assert (
        framework_assignment_candidate_id_sequence("FAC-123456")
        == 123_456
    )


def test_identifier_sequence_bounds_are_explicit() -> None:
    assert MIN_FRAMEWORK_ASSIGNMENT_SEQUENCE == 1
    assert MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE == 999_999


def test_next_agent_id_starts_at_one() -> None:
    assert next_framework_assignment_agent_candidate_id(()) == (
        "FAAC-000001"
    )


def test_next_persistent_id_starts_at_one() -> None:
    assert next_framework_assignment_candidate_id(()) == (
        "FAC-000001"
    )


def test_next_ids_do_not_reuse_gaps() -> None:
    assert next_framework_assignment_agent_candidate_id(
        ("FAAC-000001", "FAAC-000003")
    ) == "FAAC-000004"
    assert next_framework_assignment_candidate_id(
        ("FAC-000001", "FAC-000003")
    ) == "FAC-000004"


@pytest.mark.parametrize(
    "occupied",
    (
        "FAC-000001",
        42,
        None,
        ("FAC-000001", "FAC-000001"),
        ("wrong",),
    ),
)
def test_invalid_persistent_occupied_ids_are_rejected(
    occupied: object,
) -> None:
    with pytest.raises(
        FrameworkAssignmentCandidateIdAllocationError
    ):
        next_framework_assignment_candidate_id(occupied)


@pytest.mark.parametrize(
    "occupied",
    (
        "FAAC-000001",
        42,
        None,
        ("FAAC-000001", "FAAC-000001"),
        ("wrong",),
    ),
)
def test_invalid_agent_occupied_ids_are_rejected(
    occupied: object,
) -> None:
    with pytest.raises(
        FrameworkAssignmentAgentCandidateIdAllocationError
    ):
        next_framework_assignment_agent_candidate_id(occupied)


def test_exhausted_identifier_ranges_are_rejected() -> None:
    with pytest.raises(
        FrameworkAssignmentAgentCandidateIdAllocationError
    ):
        next_framework_assignment_agent_candidate_id(
            ("FAAC-999999",)
        )
    with pytest.raises(
        FrameworkAssignmentCandidateIdAllocationError
    ):
        next_framework_assignment_candidate_id(
            ("FAC-999999",)
        )


def test_assignment_constants_are_explicit() -> None:
    assert FRAMEWORK_ASSIGNMENT_STATUSES == frozenset(
        {
            "assigned",
            "unassigned",
            "ambiguous",
            "conflict",
        }
    )
    assert FRAMEWORK_ASSIGNMENT_BASIS_TYPES == frozenset(
        {
            "information_unit",
            "terminology_mapping_candidate",
            "turing_core_concept",
            "semantic_interpretation",
        }
    )
    assert FRAMEWORK_ASSIGNMENT_CONFIDENCE_LEVELS == frozenset(
        {"high", "medium", "low"}
    )
    assert FRAMEWORK_ASSIGNMENT_CONSENSUS_LEVELS == frozenset(
        {
            "unanimous",
            "majority",
            "single",
            "none",
            "incomparable",
            "incomplete",
        }
    )
    assert FRAMEWORK_ASSIGNMENT_VARIANCE_LEVELS == frozenset(
        {"low", "medium", "high"}
    )
    assert FRAMEWORK_ASSIGNMENT_REVIEW_MODES == frozenset(
        {"quick_confirmation", "detailed_review"}
    )
    assert FRAMEWORK_ASSIGNMENT_ISSUE_LEVELS == frozenset(
        {"warning", "blocking"}
    )


def test_all_public_data_types_are_frozen_and_slotted() -> None:
    data_types = (
        FrameworkAssignmentBasis,
        FrameworkAssignmentProposal,
        FrameworkAssignmentAgentCandidate,
        FrameworkAssignmentAgentResult,
        FrameworkAssignmentAgentCandidateReference,
        FrameworkAssignmentValueDistribution,
        FrameworkAssignmentConsensusOutcome,
        FrameworkAssignmentCandidate,
        FrameworkAssignmentIssue,
        FrameworkAssignmentScanResult,
    )

    for data_type in data_types:
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_agent_outputs_have_no_derived_authority_fields() -> None:
    forbidden = {
        "framework_assignment_candidate_id",
        "confidence",
        "consensus_level",
        "variance_level",
        "confirmation_required",
        "review_required",
        "recommended_review_mode",
        "persistence_eligible",
    }
    candidate_fields = {
        field.name
        for field in fields(FrameworkAssignmentAgentCandidate)
    }
    result_fields = {
        field.name
        for field in fields(FrameworkAssignmentAgentResult)
    }

    assert forbidden.isdisjoint(candidate_fields)
    assert forbidden.isdisjoint(result_fields)


def test_framework_target_is_stable_node_id_only() -> None:
    proposal_fields = {
        field.name
        for field in fields(FrameworkAssignmentProposal)
    }

    assert proposal_fields == {
        "framework_node_id",
        "assignment_bases",
        "rationale",
    }
    assert "node_name" not in proposal_fields
    assert "mapping_key" not in proposal_fields


def test_candidate_keeps_human_confirmation_boundary() -> None:
    candidate_fields = {
        field.name
        for field in fields(FrameworkAssignmentCandidate)
    }

    assert {
        "confirmation_required",
        "review_required",
        "recommended_review_mode",
    }.issubset(candidate_fields)
    assert "accepted" not in candidate_fields
    assert "approved" not in candidate_fields


def test_assignment_basis_is_versioned() -> None:
    basis_fields = {
        field.name
        for field in fields(FrameworkAssignmentBasis)
    }

    assert basis_fields == {
        "basis_type",
        "reference_id",
        "reference_version",
        "rationale",
    }


def test_candidate_preserves_upstream_versions() -> None:
    candidate_fields = {
        field.name
        for field in fields(FrameworkAssignmentCandidate)
    }

    assert {
        "framework_template_id",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
    }.issubset(candidate_fields)


def test_frozen_instance_rejects_mutation() -> None:
    basis = FrameworkAssignmentBasis(
        basis_type="information_unit",
        reference_id="IU-000001",
        reference_version="1",
        rationale="Published semantic information.",
    )

    with pytest.raises(FrozenInstanceError):
        basis.reference_id = "IU-000002"