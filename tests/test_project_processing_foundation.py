"""Tests for project-processing identifiers and foundation types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import Callable

import pytest

from modules.project_processing.errors import (
    DuplicateProcessingDecisionError,
    DuplicateProcessingEventError,
    InvalidProcessingTransitionError,
    ProcessingAttemptIdAllocationError,
    ProcessingDecisionIdAllocationError,
    ProcessingDecisionNotFoundError,
    ProcessingEventChainError,
    ProcessingEventIdAllocationError,
    ProcessingIdentifierAllocationError,
    ProcessingIntegrityError,
    ProcessingPersistenceError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingRunIdAllocationError,
    ProcessingRunNotFoundError,
    ProcessingValidationError,
    ProjectProcessingError,
    UnsafeProcessingPathError,
)
from modules.project_processing.identifiers import (
    MAX_PROCESSING_IDENTIFIER_SEQUENCE,
    MIN_PROCESSING_IDENTIFIER_SEQUENCE,
    format_processing_attempt_id,
    format_processing_decision_id,
    format_processing_event_id,
    format_processing_run_id,
    is_valid_processing_attempt_id,
    is_valid_processing_decision_id,
    is_valid_processing_event_id,
    is_valid_processing_run_id,
    next_processing_attempt_id,
    next_processing_decision_id,
    next_processing_event_id,
    next_processing_run_id,
    processing_attempt_id_sequence,
    processing_decision_id_sequence,
    processing_event_id_sequence,
    processing_run_id_sequence,
    validate_processing_attempt_id,
    validate_processing_decision_id,
    validate_processing_event_id,
    validate_processing_run_id,
)
from modules.project_processing.types import (
    ARTIFACT_LIFECYCLE_STATES,
    PROCESSING_DECISION_TYPES,
    PROCESSING_EVENT_TYPES,
    PROCESSING_ISSUE_LEVELS,
    PROCESSING_RUN_STATES,
    PROCESSING_STAGES,
    PROCESSING_WORKFLOW_PROFILES,
    PROJECT_PROCESSING_STATES,
    SOURCE_PROCESSING_DISPOSITIONS,
    DerivedProcessingRunState,
    ProcessingArtifactLifecycle,
    ProcessingArtifactReference,
    ProcessingDecision,
    ProcessingEvent,
    ProcessingIssue,
    ProcessingRunHistory,
    ProcessingRunManifest,
    ProcessingScanResult,
    ProjectProcessingSummary,
    SemanticReferenceVersion,
    SourceProcessingSummary,
)


Validator = Callable[[object], str]
ValidityChecker = Callable[[object], bool]
Formatter = Callable[[object], str]
SequenceReader = Callable[[object], int]
Allocator = Callable[[object], str]


_IDENTIFIER_CASES = (
    (
        "RUN",
        is_valid_processing_run_id,
        validate_processing_run_id,
        format_processing_run_id,
        processing_run_id_sequence,
        next_processing_run_id,
        ProcessingRunIdAllocationError,
    ),
    (
        "EVT",
        is_valid_processing_event_id,
        validate_processing_event_id,
        format_processing_event_id,
        processing_event_id_sequence,
        next_processing_event_id,
        ProcessingEventIdAllocationError,
    ),
    (
        "ATT",
        is_valid_processing_attempt_id,
        validate_processing_attempt_id,
        format_processing_attempt_id,
        processing_attempt_id_sequence,
        next_processing_attempt_id,
        ProcessingAttemptIdAllocationError,
    ),
    (
        "PD",
        is_valid_processing_decision_id,
        validate_processing_decision_id,
        format_processing_decision_id,
        processing_decision_id_sequence,
        next_processing_decision_id,
        ProcessingDecisionIdAllocationError,
    ),
)


def test_error_hierarchy_is_explicit() -> None:
    direct_errors = (
        ProcessingValidationError,
        ProcessingIntegrityError,
        ProcessingReferenceError,
        ProcessingPersistenceError,
        ProcessingRunNotFoundError,
        ProcessingDecisionNotFoundError,
        ProcessingIdentifierAllocationError,
        UnsafeProcessingPathError,
    )

    assert all(
        issubclass(error, ProjectProcessingError)
        for error in direct_errors
    )

    allocation_errors = (
        ProcessingRunIdAllocationError,
        ProcessingEventIdAllocationError,
        ProcessingAttemptIdAllocationError,
        ProcessingDecisionIdAllocationError,
    )

    assert all(
        issubclass(
            error,
            ProcessingIdentifierAllocationError,
        )
        for error in allocation_errors
    )

    assert issubclass(
        InvalidProcessingTransitionError,
        ProcessingValidationError,
    )

    integrity_errors = (
        DuplicateProcessingEventError,
        DuplicateProcessingDecisionError,
        ProcessingEventChainError,
        ProcessingRecoveryRequiredError,
    )

    assert all(
        issubclass(error, ProcessingIntegrityError)
        for error in integrity_errors
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
def test_valid_processing_identifiers(
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
        "RUN-000000",
        "RUN-00001",
        "RUN-1000000",
        "run-000001",
        "RUN_000001",
        " RUN-000001",
    ),
)
def test_invalid_processing_identifiers(
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

    with pytest.raises(ProcessingValidationError):
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
def test_invalid_processing_identifier_sequences(
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

    with pytest.raises(ProcessingValidationError):
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
def test_next_identifier_does_not_reuse_gaps(
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

    assert allocator(
        (
            f"{prefix}-000001",
            f"{prefix}-000003",
        )
    ) == f"{prefix}-000004"


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
def test_invalid_occupied_identifiers_are_rejected(
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

    invalid_inputs = (
        f"{prefix}-000001",
        42,
        None,
        (
            f"{prefix}-000001",
            f"{prefix}-000001",
        ),
        ("wrong",),
        (f"{prefix}-999999",),
    )

    for invalid_input in invalid_inputs:
        with pytest.raises(allocation_error):
            allocator(invalid_input)


def test_identifier_bounds_are_explicit() -> None:
    assert MIN_PROCESSING_IDENTIFIER_SEQUENCE == 1
    assert MAX_PROCESSING_IDENTIFIER_SEQUENCE == 999_999


def test_processing_vocabularies_are_closed() -> None:
    assert PROCESSING_RUN_STATES == frozenset(
        {
            "created",
            "running",
            "awaiting_review",
            "blocked",
            "failed",
            "completed",
            "superseded",
        }
    )

    assert PROCESSING_STAGES == frozenset(
        {
            "source_projection",
            "semantic_extraction",
            "semantic_consensus",
            "terminology_mapping",
            "framework_assignment",
            "human_review",
            "publication",
        }
    )

    assert PROCESSING_WORKFLOW_PROFILES == frozenset(
        {
            "engineering_source_processing",
            "context_only_processing",
        }
    )

    assert SOURCE_PROCESSING_DISPOSITIONS == frozenset(
        {
            "in_scope",
            "context_only",
            "out_of_scope",
        }
    )

    assert PROCESSING_DECISION_TYPES == frozenset(
        {
            "source_disposition",
        }
    )

    assert ARTIFACT_LIFECYCLE_STATES == frozenset(
        {
            "active",
            "superseded",
            "invalidated",
        }
    )

    assert PROJECT_PROCESSING_STATES == frozenset(
        {
            "empty",
            "not_started",
            "in_progress",
            "awaiting_review",
            "attention_required",
            "partially_processed",
            "processed",
        }
    )

    assert PROCESSING_ISSUE_LEVELS == frozenset(
        {
            "warning",
            "blocking",
        }
    )


def test_processing_event_types_are_complete() -> None:
    assert PROCESSING_EVENT_TYPES == frozenset(
        {
            "run_created",
            "stage_started",
            "stage_completed",
            "review_requested",
            "review_resolved",
            "run_blocked",
            "run_failed",
            "retry_started",
            "artifact_published",
            "artifact_invalidated",
            "artifact_superseded",
            "recovery_required",
            "recovery_completed",
            "run_completed",
            "run_superseded",
        }
    )


def test_all_public_data_types_are_frozen_and_slotted() -> None:
    data_types = (
        SemanticReferenceVersion,
        ProcessingArtifactReference,
        ProcessingRunManifest,
        ProcessingEvent,
        ProcessingDecision,
        ProcessingArtifactLifecycle,
        ProcessingIssue,
        ProcessingRunHistory,
        DerivedProcessingRunState,
        SourceProcessingSummary,
        ProjectProcessingSummary,
        ProcessingScanResult,
    )

    for data_type in data_types:
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_run_manifest_binds_one_source_and_versions() -> None:
    names = {
        field.name
        for field in fields(ProcessingRunManifest)
    }

    assert {
        "project_id",
        "processing_run_id",
        "source_id",
        "source_sha256",
        "source_role_snapshot",
        "workflow_profile",
        "configuration_fingerprint",
        "framework_template_id",
        "framework_template_version",
        "semantic_reference_versions",
        "supersedes_run_id",
    }.issubset(names)

    assert "source_ids" not in names
    assert "current_state" not in names
    assert "approved_input_id" not in names


def test_processing_event_contains_chain_and_artifact_evidence() -> None:
    names = {
        field.name
        for field in fields(ProcessingEvent)
    }

    assert {
        "event_id",
        "event_sequence",
        "previous_state",
        "next_state",
        "processing_stage",
        "attempt_id",
        "artifact_references",
        "previous_event_fingerprint",
        "event_fingerprint",
    }.issubset(names)


def test_processing_decision_is_operational_only() -> None:
    names = {
        field.name
        for field in fields(ProcessingDecision)
    }

    assert {
        "source_id",
        "source_sha256",
        "disposition",
        "reviewer_identity",
        "decision_fingerprint",
    }.issubset(names)

    assert "engineering_approval" not in names
    assert "approved_input_id" not in names
    assert "generation_ready" not in names


def test_project_summary_preserves_explicit_counts() -> None:
    names = {
        field.name
        for field in fields(ProjectProcessingSummary)
    }

    assert {
        "project_state",
        "total_sources",
        "in_scope_sources",
        "context_only_sources",
        "out_of_scope_sources",
        "not_started_sources",
        "running_sources",
        "awaiting_review_sources",
        "blocked_sources",
        "failed_sources",
        "completed_sources",
        "superseded_runs",
        "invalidated_artifacts",
    }.issubset(names)

    assert "approved_readiness" not in names
    assert "generation_ready" not in names


def test_frozen_processing_reference_rejects_mutation() -> None:
    reference = ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id="IU-000001",
        content_fingerprint="a" * 64,
        repository_relative_path=(
            "data/projects/318604/semantics/"
            "information_units/IU-000001.json"
        ),
    )

    with pytest.raises(FrozenInstanceError):
        reference.artifact_id = "IU-000002"