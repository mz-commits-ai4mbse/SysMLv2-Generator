"""Public API contract tests for terminology mapping."""

from __future__ import annotations

from dataclasses import is_dataclass
import inspect

import modules.terminology_mapping as terminology_mapping
from modules.terminology_mapping import (
    TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION,
    TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION,
    TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION,
    TERMINOLOGY_MAPPING_NORMALIZATION_ID,
    TERMINOLOGY_MAPPING_NORMALIZATION_VERSION,
    TERMINOLOGY_MAPPINGS_DIRECTORY_NAME,
    TerminologyMappingAgentCandidate,
    TerminologyMappingAgentCandidateReference,
    TerminologyMappingAgentResult,
    TerminologyMappingBasis,
    TerminologyMappingCandidate,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingConsensusResult,
    TerminologyMappingIssue,
    TerminologyMappingProposal,
    TerminologyMappingReferenceValidationResult,
    TerminologyMappingRepository,
    TerminologyMappingScanResult,
    TerminologyMappingTarget,
    TerminologyMappingValueDistribution,
    TerminologyOccurrence,
    analyze_terminology_mapping_consensus,
    create_terminology_mapping_agent_result,
    create_terminology_mapping_candidate,
    next_terminology_mapping_candidate_id,
    terminology_mapping_candidate_from_json,
    terminology_mapping_candidate_to_json,
    validate_terminology_mapping_references,
)


EXPECTED_SCHEMA_VERSION = "1.0.0"


def test_public_schema_versions_are_explicit() -> None:
    assert TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION == (
        EXPECTED_SCHEMA_VERSION
    )
    assert TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION == (
        EXPECTED_SCHEMA_VERSION
    )
    assert TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION == (
        EXPECTED_SCHEMA_VERSION
    )
    assert TERMINOLOGY_MAPPING_NORMALIZATION_VERSION == (
        EXPECTED_SCHEMA_VERSION
    )


def test_normalization_identity_is_public() -> None:
    assert TERMINOLOGY_MAPPING_NORMALIZATION_ID == (
        "unicode_nfkc_whitespace_casefold"
    )


def test_persistence_directory_is_public() -> None:
    assert TERMINOLOGY_MAPPINGS_DIRECTORY_NAME == (
        "terminology_mappings"
    )


def test_public_data_types_are_frozen_and_slotted() -> None:
    data_types = (
        TerminologyOccurrence,
        TerminologyMappingTarget,
        TerminologyMappingBasis,
        TerminologyMappingProposal,
        TerminologyMappingAgentCandidate,
        TerminologyMappingAgentResult,
        TerminologyMappingAgentCandidateReference,
        TerminologyMappingValueDistribution,
        TerminologyMappingConsensusOutcome,
        TerminologyMappingCandidate,
        TerminologyMappingIssue,
        TerminologyMappingScanResult,
        TerminologyMappingConsensusResult,
        TerminologyMappingReferenceValidationResult,
    )

    for data_type in data_types:
        assert is_dataclass(data_type)
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_main_workflow_functions_are_public() -> None:
    functions = (
        create_terminology_mapping_agent_result,
        analyze_terminology_mapping_consensus,
        create_terminology_mapping_candidate,
        terminology_mapping_candidate_to_json,
        terminology_mapping_candidate_from_json,
        validate_terminology_mapping_references,
        next_terminology_mapping_candidate_id,
    )

    assert all(callable(function) for function in functions)


def test_repository_is_public_class() -> None:
    assert inspect.isclass(TerminologyMappingRepository)


def test_all_exports_are_unique() -> None:
    exported = terminology_mapping.__all__

    assert isinstance(exported, tuple)
    assert len(exported) == len(set(exported))


def test_every_declared_export_exists() -> None:
    assert all(
        hasattr(terminology_mapping, name)
        for name in terminology_mapping.__all__
    )


def test_private_implementation_helpers_are_not_exported() -> None:
    assert all(
        not name.startswith("_")
        for name in terminology_mapping.__all__
    )
    assert "_default_clock" not in terminology_mapping.__all__
    assert "_require_supported_inputs" not in (
        terminology_mapping.__all__
    )


def test_public_api_preserves_human_authority_boundary() -> None:
    forbidden_mutation_names = {
        "accept_terminology_mapping",
        "approve_terminology_mapping",
        "mutate_project_glossary",
        "publish_to_project_glossary",
        "update_turing_core",
    }

    assert forbidden_mutation_names.isdisjoint(
        terminology_mapping.__all__
    )