"""Tests for Human Review Workspace errors and identifiers."""

from __future__ import annotations

from typing import Callable

import pytest

from modules.review_workspace.errors import (
    DuplicateReviewRevisionError,
    DuplicateScopedReviewActionError,
    InvalidReviewVersionTransitionError,
    ReviewDocumentIdAllocationError,
    ReviewDocumentNotFoundError,
    ReviewDocumentVersionIdAllocationError,
    ReviewDocumentVersionNotFoundError,
    ReviewFinalizationBlockedError,
    ReviewIdentifierAllocationError,
    ReviewIntegrityError,
    ReviewItemIdAllocationError,
    ReviewItemNotFoundError,
    ReviewPersistenceError,
    ReviewRecoveryRequiredError,
    ReviewReferenceError,
    ReviewRevisionIdAllocationError,
    ReviewRevisionNotFoundError,
    ReviewValidationError,
    ReviewWorkspaceError,
    ScopedReviewActionIdAllocationError,
    StaleReviewRevisionError,
    UnsafeReviewWorkspacePathError,
)
from modules.review_workspace.identifiers import (
    MAX_REVIEW_IDENTIFIER_SEQUENCE,
    MIN_REVIEW_IDENTIFIER_SEQUENCE,
    format_review_document_id,
    format_review_document_version_id,
    format_review_item_id,
    format_review_revision_id,
    format_scoped_review_action_id,
    is_valid_review_document_id,
    is_valid_review_document_version_id,
    is_valid_review_item_id,
    is_valid_review_revision_id,
    is_valid_scoped_review_action_id,
    next_review_document_id,
    next_review_document_version_id,
    next_review_item_id,
    next_review_revision_id,
    next_scoped_review_action_id,
    review_document_id_sequence,
    review_document_version_id_sequence,
    review_item_id_sequence,
    review_revision_id_sequence,
    scoped_review_action_id_sequence,
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
    validate_review_revision_id,
    validate_scoped_review_action_id,
)


Validator = Callable[[object], str]
ValidityChecker = Callable[[object], bool]
Formatter = Callable[[object], str]
SequenceReader = Callable[[object], int]
Allocator = Callable[[object], str]


_IDENTIFIER_CASES = (
    (
        "RVD",
        is_valid_review_document_id,
        validate_review_document_id,
        format_review_document_id,
        review_document_id_sequence,
        next_review_document_id,
        ReviewDocumentIdAllocationError,
    ),
    (
        "RVV",
        is_valid_review_document_version_id,
        validate_review_document_version_id,
        format_review_document_version_id,
        review_document_version_id_sequence,
        next_review_document_version_id,
        ReviewDocumentVersionIdAllocationError,
    ),
    (
        "RVR",
        is_valid_review_revision_id,
        validate_review_revision_id,
        format_review_revision_id,
        review_revision_id_sequence,
        next_review_revision_id,
        ReviewRevisionIdAllocationError,
    ),
    (
        "RIT",
        is_valid_review_item_id,
        validate_review_item_id,
        format_review_item_id,
        review_item_id_sequence,
        next_review_item_id,
        ReviewItemIdAllocationError,
    ),
    (
        "SRA",
        is_valid_scoped_review_action_id,
        validate_scoped_review_action_id,
        format_scoped_review_action_id,
        scoped_review_action_id_sequence,
        next_scoped_review_action_id,
        ScopedReviewActionIdAllocationError,
    ),
)


def test_error_hierarchy_is_explicit() -> None:
    direct_errors = (
        ReviewValidationError,
        ReviewIntegrityError,
        ReviewReferenceError,
        ReviewPersistenceError,
        ReviewIdentifierAllocationError,
        UnsafeReviewWorkspacePathError,
    )

    assert all(
        issubclass(error, ReviewWorkspaceError)
        for error in direct_errors
    )

    reference_errors = (
        ReviewDocumentNotFoundError,
        ReviewDocumentVersionNotFoundError,
        ReviewRevisionNotFoundError,
        ReviewItemNotFoundError,
    )

    assert all(
        issubclass(error, ReviewReferenceError)
        for error in reference_errors
    )

    allocation_errors = (
        ReviewDocumentIdAllocationError,
        ReviewDocumentVersionIdAllocationError,
        ReviewRevisionIdAllocationError,
        ReviewItemIdAllocationError,
        ScopedReviewActionIdAllocationError,
    )

    assert all(
        issubclass(
            error,
            ReviewIdentifierAllocationError,
        )
        for error in allocation_errors
    )

    integrity_errors = (
        DuplicateReviewRevisionError,
        DuplicateScopedReviewActionError,
        StaleReviewRevisionError,
        ReviewFinalizationBlockedError,
        ReviewRecoveryRequiredError,
    )

    assert all(
        issubclass(error, ReviewIntegrityError)
        for error in integrity_errors
    )

    assert issubclass(
        InvalidReviewVersionTransitionError,
        ReviewValidationError,
    )


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_valid_review_workspace_identifiers(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del allocator
    del allocation_error

    values = (
        f"{prefix}-000001",
        f"{prefix}-123456",
        f"{prefix}-999999",
    )

    for value in values:
        assert is_valid(value)
        assert validator(value) == value

    assert formatter(42) == f"{prefix}-000042"
    assert sequence_reader(
        f"{prefix}-654321"
    ) == 654_321


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        True,
        "",
        "XXX-000001",
        "000001",
        "RVD-00001",
        "RVD-1000000",
        "rvd-000001",
        "RVD_000001",
        " RVD-000001",
        "RVD-000001 ",
    ),
)
def test_invalid_review_workspace_identifiers(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
    value: object,
) -> None:
    del prefix
    del formatter
    del sequence_reader
    del allocator
    del allocation_error

    assert not is_valid(value)

    with pytest.raises(ReviewValidationError):
        validator(value)


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_zero_sequence_is_rejected(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del formatter
    del sequence_reader
    del allocator
    del allocation_error

    value = f"{prefix}-000000"

    assert not is_valid(value)

    with pytest.raises(ReviewValidationError):
        validator(value)


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
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
def test_invalid_identifier_sequences_are_rejected(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
    sequence: object,
) -> None:
    del prefix
    del is_valid
    del validator
    del sequence_reader
    del allocator
    del allocation_error

    with pytest.raises(ReviewValidationError):
        formatter(sequence)


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_identifier_allocation_is_sequential_and_does_not_reuse_gaps(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader
    del allocation_error

    assert allocator(()) == f"{prefix}-000001"

    occupied = (
        f"{prefix}-000001",
        f"{prefix}-000003",
        f"{prefix}-000008",
    )

    assert allocator(occupied) == f"{prefix}-000009"


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_identifier_allocation_accepts_generators(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader
    del allocation_error

    occupied = (
        f"{prefix}-{sequence:06d}"
        for sequence in (1, 4, 7)
    )

    assert allocator(occupied) == f"{prefix}-000008"


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_identifier_allocation_rejects_unsafe_input(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader

    with pytest.raises(allocation_error):
        allocator(f"{prefix}-000001")

    with pytest.raises(allocation_error):
        allocator(None)

    with pytest.raises(allocation_error):
        allocator(
            (
                f"{prefix}-000001",
                f"{prefix}-000001",
            )
        )

    with pytest.raises(allocation_error):
        allocator(
            (
                f"{prefix}-000001",
                "INVALID-000002",
            )
        )


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_identifier_allocation_detects_exhaustion(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader

    with pytest.raises(allocation_error):
        allocator(
            (
                f"{prefix}-"
                f"{MAX_REVIEW_IDENTIFIER_SEQUENCE:06d}",
            )
        )


def test_review_identifier_limits_are_explicit() -> None:
    assert MIN_REVIEW_IDENTIFIER_SEQUENCE == 1
    assert MAX_REVIEW_IDENTIFIER_SEQUENCE == 999_999
