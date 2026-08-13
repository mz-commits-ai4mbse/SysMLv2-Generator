from __future__ import annotations

import pytest

from modules.internal_model import (
    InternalEngineeringModelIdAllocationError,
    InternalModelElementIdAllocationError,
    InternalModelRelationshipIdAllocationError,
    InternalModelValidationError,
    format_internal_engineering_model_id,
    format_internal_model_element_id,
    format_internal_model_relationship_id,
    internal_engineering_model_id_sequence,
    internal_model_element_id_sequence,
    internal_model_relationship_id_sequence,
    is_valid_internal_engineering_model_id,
    is_valid_internal_model_element_id,
    is_valid_internal_model_relationship_id,
    next_internal_engineering_model_id,
    next_internal_model_element_id,
    next_internal_model_relationship_id,
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)


@pytest.mark.parametrize(
    ("validator", "valid", "invalid"),
    [
        (
            validate_internal_engineering_model_id,
            "IEM-000001",
            "IEM-000000",
        ),
        (
            validate_internal_model_element_id,
            "IME-000001",
            "IME-000000",
        ),
        (
            validate_internal_model_relationship_id,
            "IMR-000001",
            "IMR-000000",
        ),
    ],
)
def test_validators_accept_positive_six_digit_ids(
    validator,
    valid,
    invalid,
):
    assert validator(valid) == valid
    with pytest.raises(InternalModelValidationError):
        validator(invalid)


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_internal_engineering_model_id, "IEM-1"),
        (validate_internal_engineering_model_id, "iem-000001"),
        (validate_internal_engineering_model_id, None),
        (validate_internal_model_element_id, "MCE-000001"),
        (validate_internal_model_element_id, "IME-1000000"),
        (validate_internal_model_element_id, 1),
        (validate_internal_model_relationship_id, "IMR-00001"),
        (validate_internal_model_relationship_id, "IMR-ABCDEF"),
        (validate_internal_model_relationship_id, b"IMR-000001"),
    ],
)
def test_validators_reject_invalid_values(validator, value):
    with pytest.raises(InternalModelValidationError):
        validator(value)


@pytest.mark.parametrize(
    ("predicate", "valid", "invalid"),
    [
        (
            is_valid_internal_engineering_model_id,
            "IEM-999999",
            "IEM-000000",
        ),
        (
            is_valid_internal_model_element_id,
            "IME-999999",
            "IME-000000",
        ),
        (
            is_valid_internal_model_relationship_id,
            "IMR-999999",
            "IMR-000000",
        ),
    ],
)
def test_is_valid_helpers(predicate, valid, invalid):
    assert predicate(valid) is True
    assert predicate(invalid) is False
    assert predicate(None) is False


@pytest.mark.parametrize(
    ("formatter", "sequence", "expected"),
    [
        (format_internal_engineering_model_id, 1, "IEM-000001"),
        (format_internal_engineering_model_id, 999999, "IEM-999999"),
        (format_internal_model_element_id, 42, "IME-000042"),
        (format_internal_model_relationship_id, 7, "IMR-000007"),
    ],
)
def test_formatters(formatter, sequence, expected):
    assert formatter(sequence) == expected


@pytest.mark.parametrize(
    ("formatter", "sequence"),
    [
        (format_internal_engineering_model_id, 0),
        (format_internal_engineering_model_id, 1_000_000),
        (format_internal_model_element_id, True),
        (format_internal_model_element_id, 1.0),
        (format_internal_model_relationship_id, -1),
        (format_internal_model_relationship_id, "1"),
    ],
)
def test_formatters_reject_invalid_sequences(formatter, sequence):
    with pytest.raises(InternalModelValidationError):
        formatter(sequence)


def test_sequence_readers():
    assert internal_engineering_model_id_sequence("IEM-000042") == 42
    assert internal_model_element_id_sequence("IME-000043") == 43
    assert internal_model_relationship_id_sequence("IMR-000044") == 44


@pytest.mark.parametrize(
    ("allocator", "occupied", "expected"),
    [
        (next_internal_engineering_model_id, (), "IEM-000001"),
        (
            next_internal_engineering_model_id,
            ("IEM-000001", "IEM-000004"),
            "IEM-000005",
        ),
        (
            next_internal_model_element_id,
            ("IME-000002", "IME-000010"),
            "IME-000011",
        ),
        (
            next_internal_model_relationship_id,
            ("IMR-000003",),
            "IMR-000004",
        ),
    ],
)
def test_allocators_use_highest_sequence_without_gap_reuse(
    allocator,
    occupied,
    expected,
):
    assert allocator(occupied) == expected


@pytest.mark.parametrize(
    ("allocator", "occupied", "error_type"),
    [
        (
            next_internal_engineering_model_id,
            ("IEM-000001", "IEM-000001"),
            InternalEngineeringModelIdAllocationError,
        ),
        (
            next_internal_model_element_id,
            ("IME-000001", "bad"),
            InternalModelElementIdAllocationError,
        ),
        (
            next_internal_model_relationship_id,
            "IMR-000001",
            InternalModelRelationshipIdAllocationError,
        ),
    ],
)
def test_allocators_fail_closed_on_invalid_occupied_values(
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
            next_internal_engineering_model_id,
            ("IEM-999999",),
            InternalEngineeringModelIdAllocationError,
        ),
        (
            next_internal_model_element_id,
            ("IME-999999",),
            InternalModelElementIdAllocationError,
        ),
        (
            next_internal_model_relationship_id,
            ("IMR-999999",),
            InternalModelRelationshipIdAllocationError,
        ),
    ],
)
def test_allocators_fail_when_range_is_exhausted(
    allocator,
    occupied,
    error_type,
):
    with pytest.raises(error_type):
        allocator(occupied)
