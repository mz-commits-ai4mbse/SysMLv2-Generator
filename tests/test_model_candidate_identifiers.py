"""Tests for stable Phase-H Model Candidate identifiers."""

import pytest

from modules.model_candidates import (
    ModelCandidateSetIdAllocationError,
    ModelCandidateValidationError,
    ModelElementCandidateIdAllocationError,
    ModelRelationshipCandidateIdAllocationError,
    format_model_candidate_set_id,
    format_model_element_candidate_id,
    format_model_relationship_candidate_id,
    is_valid_model_candidate_set_id,
    is_valid_model_element_candidate_id,
    is_valid_model_relationship_candidate_id,
    model_candidate_set_id_sequence,
    model_element_candidate_id_sequence,
    model_relationship_candidate_id_sequence,
    next_model_candidate_set_id,
    next_model_element_candidate_id,
    next_model_relationship_candidate_id,
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)


@pytest.mark.parametrize(
    ("value", "validator", "predicate", "sequence_reader", "sequence"),
    [
        (
            "MCS-000001",
            validate_model_candidate_set_id,
            is_valid_model_candidate_set_id,
            model_candidate_set_id_sequence,
            1,
        ),
        (
            "MCE-000042",
            validate_model_element_candidate_id,
            is_valid_model_element_candidate_id,
            model_element_candidate_id_sequence,
            42,
        ),
        (
            "MCR-999999",
            validate_model_relationship_candidate_id,
            is_valid_model_relationship_candidate_id,
            model_relationship_candidate_id_sequence,
            999_999,
        ),
    ],
)
def test_valid_identifiers(
    value,
    validator,
    predicate,
    sequence_reader,
    sequence,
):
    assert predicate(value) is True
    assert validator(value) == value
    assert sequence_reader(value) == sequence


@pytest.mark.parametrize(
    ("value", "predicate"),
    [
        ("MCS-000000", is_valid_model_candidate_set_id),
        ("MCS-00001", is_valid_model_candidate_set_id),
        ("mcs-000001", is_valid_model_candidate_set_id),
        ("MCE-000000", is_valid_model_element_candidate_id),
        ("MCE-1000000", is_valid_model_element_candidate_id),
        ("MCR-000000", is_valid_model_relationship_candidate_id),
        ("MCR-ABCDEF", is_valid_model_relationship_candidate_id),
        (None, is_valid_model_candidate_set_id),
        (42, is_valid_model_element_candidate_id),
    ],
)
def test_invalid_identifiers_return_false(value, predicate):
    assert predicate(value) is False


@pytest.mark.parametrize(
    ("value", "validator"),
    [
        ("MCS-000000", validate_model_candidate_set_id),
        ("MCS-00001", validate_model_candidate_set_id),
        ("MCE-000000", validate_model_element_candidate_id),
        ("MCE-ABCDEF", validate_model_element_candidate_id),
        ("MCR-000000", validate_model_relationship_candidate_id),
        ("MCR-1000000", validate_model_relationship_candidate_id),
        (True, validate_model_candidate_set_id),
    ],
)
def test_invalid_identifiers_raise(value, validator):
    with pytest.raises(ModelCandidateValidationError):
        validator(value)


@pytest.mark.parametrize(
    ("formatter", "sequence", "expected"),
    [
        (format_model_candidate_set_id, 1, "MCS-000001"),
        (format_model_element_candidate_id, 42, "MCE-000042"),
        (
            format_model_relationship_candidate_id,
            999_999,
            "MCR-999999",
        ),
    ],
)
def test_format_identifiers(formatter, sequence, expected):
    assert formatter(sequence) == expected


@pytest.mark.parametrize(
    "formatter",
    [
        format_model_candidate_set_id,
        format_model_element_candidate_id,
        format_model_relationship_candidate_id,
    ],
)
@pytest.mark.parametrize("sequence", [0, 1_000_000, True, "1"])
def test_format_rejects_invalid_sequences(formatter, sequence):
    with pytest.raises(ModelCandidateValidationError):
        formatter(sequence)


@pytest.mark.parametrize(
    ("allocator", "occupied", "expected"),
    [
        (next_model_candidate_set_id, (), "MCS-000001"),
        (
            next_model_candidate_set_id,
            ("MCS-000001", "MCS-000003"),
            "MCS-000004",
        ),
        (
            next_model_element_candidate_id,
            ("MCE-000002", "MCE-000001"),
            "MCE-000003",
        ),
        (
            next_model_relationship_candidate_id,
            ("MCR-000099",),
            "MCR-000100",
        ),
    ],
)
def test_next_identifier_uses_highest_sequence(
    allocator,
    occupied,
    expected,
):
    assert allocator(occupied) == expected


@pytest.mark.parametrize(
    ("allocator", "occupied", "error_type"),
    [
        (
            next_model_candidate_set_id,
            ("MCS-000001", "MCS-000001"),
            ModelCandidateSetIdAllocationError,
        ),
        (
            next_model_element_candidate_id,
            ("MCE-000001", "bad"),
            ModelElementCandidateIdAllocationError,
        ),
        (
            next_model_relationship_candidate_id,
            "MCR-000001",
            ModelRelationshipCandidateIdAllocationError,
        ),
    ],
)
def test_next_identifier_rejects_unsafe_occupied_values(
    allocator,
    occupied,
    error_type,
):
    with pytest.raises(error_type):
        allocator(occupied)


@pytest.mark.parametrize(
    ("allocator", "occupied", "error_type"),
    [
        (
            next_model_candidate_set_id,
            ("MCS-999999",),
            ModelCandidateSetIdAllocationError,
        ),
        (
            next_model_element_candidate_id,
            ("MCE-999999",),
            ModelElementCandidateIdAllocationError,
        ),
        (
            next_model_relationship_candidate_id,
            ("MCR-999999",),
            ModelRelationshipCandidateIdAllocationError,
        ),
    ],
)
def test_identifier_ranges_exhaust_safely(
    allocator,
    occupied,
    error_type,
):
    with pytest.raises(error_type):
        allocator(occupied)
