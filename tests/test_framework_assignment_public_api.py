"""Public API contract tests for Framework Assignment."""

from __future__ import annotations

from dataclasses import is_dataclass
import inspect

import modules.framework_assignment as framework_assignment
from modules.framework_assignment import (
    FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME,
    FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION,
    FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION,
    FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION,
    FRAMEWORK_ASSIGNMENT_SIGNATURE_ID,
    FRAMEWORK_ASSIGNMENT_SIGNATURE_VERSION,
    FrameworkAssignmentAgentCandidate,
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentAgentResult,
    FrameworkAssignmentBasis,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentConsensusResult,
    FrameworkAssignmentIssue,
    FrameworkAssignmentProposal,
    FrameworkAssignmentReferenceValidationResult,
    FrameworkAssignmentRepository,
    FrameworkAssignmentScanResult,
    FrameworkAssignmentValueDistribution,
    analyze_framework_assignment_consensus,
    create_framework_assignment_agent_result,
    create_framework_assignment_candidate,
    framework_assignment_candidate_from_json,
    framework_assignment_candidate_to_json,
    next_framework_assignment_candidate_id,
    validate_framework_assignment_references,
)


def test_public_schema_versions_are_explicit() -> None:
    expected = "1.0.0"

    assert FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION == expected
    assert FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION == expected
    assert FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION == expected
    assert FRAMEWORK_ASSIGNMENT_SIGNATURE_VERSION == expected


def test_signature_identity_is_public() -> None:
    assert FRAMEWORK_ASSIGNMENT_SIGNATURE_ID == (
        "assignment_status_and_framework_node_set"
    )


def test_persistence_directory_is_public() -> None:
    assert FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME == (
        "framework_assignments"
    )


def test_public_data_types_are_frozen_and_slotted() -> None:
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
        FrameworkAssignmentConsensusResult,
        FrameworkAssignmentReferenceValidationResult,
    )

    for data_type in data_types:
        assert is_dataclass(data_type)
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_main_workflow_functions_are_public() -> None:
    functions = (
        create_framework_assignment_agent_result,
        analyze_framework_assignment_consensus,
        create_framework_assignment_candidate,
        framework_assignment_candidate_to_json,
        framework_assignment_candidate_from_json,
        validate_framework_assignment_references,
        next_framework_assignment_candidate_id,
    )

    assert all(callable(function) for function in functions)


def test_repository_is_public_class() -> None:
    assert inspect.isclass(FrameworkAssignmentRepository)


def test_all_exports_are_unique() -> None:
    exported = framework_assignment.__all__

    assert isinstance(exported, tuple)
    assert len(exported) == len(set(exported))


def test_every_declared_export_exists() -> None:
    assert all(
        hasattr(framework_assignment, name)
        for name in framework_assignment.__all__
    )


def test_private_helpers_are_not_exported() -> None:
    assert all(
        not name.startswith("_")
        for name in framework_assignment.__all__
    )
    assert "_default_clock" not in framework_assignment.__all__
    assert "_analyze_votes" not in framework_assignment.__all__


def test_public_api_preserves_human_authority_boundary() -> None:
    forbidden = {
        "accept_framework_assignment",
        "approve_framework_assignment",
        "mutate_framework_template",
        "publish_to_sysml",
        "update_information_unit",
    }

    assert forbidden.isdisjoint(framework_assignment.__all__)