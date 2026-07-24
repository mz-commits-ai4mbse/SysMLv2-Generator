"""Tests for persisted terminology mapping candidate manifests."""

from __future__ import annotations

from dataclasses import fields, replace
import json

import pytest

from modules.terminology_mapping.agent_manifest import (
    create_terminology_mapping_basis,
    create_terminology_mapping_proposal,
    create_terminology_mapping_target,
)
from modules.terminology_mapping.analyzer import (
    TerminologyMappingConsensusResult,
)
from modules.terminology_mapping.candidate_manifest import (
    TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION,
    calculate_terminology_mapping_fingerprint,
    create_terminology_mapping_candidate,
    parse_terminology_mapping_candidate,
    terminology_mapping_candidate_from_json,
    terminology_mapping_candidate_to_dict,
    terminology_mapping_candidate_to_json,
    validate_terminology_mapping_candidate,
)
from modules.terminology_mapping.errors import (
    TerminologyMappingIntegrityError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from modules.terminology_mapping.types import (
    TerminologyMappingAgentCandidateReference,
    TerminologyMappingCandidate,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingProposal,
    TerminologyOccurrence,
)


PROJECT_ID = "318604"
TIMESTAMP = "2026-07-24T15:00:00Z"


def mapping_proposal() -> TerminologyMappingProposal:
    target = create_terminology_mapping_target(
        target_kind="project_concept",
        display_label="Pump",
        project_concept_id="PC-000001",
        project_concept_revision=1,
    )
    basis = create_terminology_mapping_basis(
        basis_type="accepted_project_glossary",
        reference_id=f"{PROJECT_ID}/PC-000001/revision/1",
        reference_version="1",
        rationale="Accepted project terminology.",
    )
    return create_terminology_mapping_proposal(
        mapping_relation="exact_match",
        target=target,
        mapping_bases=(basis,),
        rationale="The term matches the accepted project concept.",
    )


def consensus_outcome(
    *,
    status: str = "mapped",
    proposals: tuple[TerminologyMappingProposal, ...]
    | None = None,
    confidence: str = "high",
    review_required: bool = False,
    persistence_eligible: bool = True,
) -> TerminologyMappingConsensusOutcome:
    return TerminologyMappingConsensusOutcome(
        occurrence=TerminologyOccurrence(
            information_unit_id="IU-000001",
            text_field="interpreted_statement",
            start_offset=4,
            end_offset=8,
            term_text="pump",
        ),
        mapping_status=status,
        selected_proposals=(
            (mapping_proposal(),)
            if proposals is None
            else proposals
        ),
        candidate_references=(
            TerminologyMappingAgentCandidateReference(
                persona_id="persona-a",
                agent_id="agent-a",
                persona_run_index=1,
                terminology_mapping_agent_candidate_id=(
                    "TMAC-000001"
                ),
            ),
            TerminologyMappingAgentCandidateReference(
                persona_id="persona-b",
                agent_id="agent-b",
                persona_run_index=1,
                terminology_mapping_agent_candidate_id=(
                    "TMAC-000001"
                ),
            ),
        ),
        value_distribution=(),
        consensus_level="unanimous",
        variance_level="low",
        confidence=confidence,
        total_personas=2,
        supporting_personas=("persona-a", "persona-b"),
        dissenting_personas=(),
        omitting_personas=(),
        confirmation_required=True,
        review_required=review_required,
        recommended_review_mode=(
            "detailed_review"
            if review_required
            else "quick_confirmation"
        ),
        persistence_eligible=persistence_eligible,
        confidence_rationale="Two of two personas agree.",
    )


def consensus_result(
    outcome: TerminologyMappingConsensusOutcome | None = None,
) -> TerminologyMappingConsensusResult:
    selected = consensus_outcome() if outcome is None else outcome
    return TerminologyMappingConsensusResult(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
        team_id="terminology-team",
        required_personas=("persona-a", "persona-b"),
        persona_run_expectations=(
            ("persona-a", 1),
            ("persona-b", 1),
        ),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        ontology_registry_version="1.0.0",
        reference_concept_index_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        outcomes=(selected,),
        issues=(),
        created_at="2026-07-24T14:00:00Z",
    )


def candidate(
    *,
    candidate_id: str = "TMC-000001",
    outcome: TerminologyMappingConsensusOutcome | None = None,
    timestamp: str = TIMESTAMP,
) -> TerminologyMappingCandidate:
    selected = consensus_outcome() if outcome is None else outcome
    return create_terminology_mapping_candidate(
        consensus_result=consensus_result(selected),
        outcome=selected,
        terminology_mapping_candidate_id=candidate_id,
        timestamp=timestamp,
    )


def payload() -> dict[str, object]:
    return terminology_mapping_candidate_to_dict(candidate())


def test_schema_version_is_explicit() -> None:
    assert TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION == "1.0.0"


def test_candidate_is_frozen_and_slotted() -> None:
    assert TerminologyMappingCandidate.__dataclass_params__.frozen
    assert TerminologyMappingCandidate.__slots__


def test_candidate_contains_no_human_decision() -> None:
    names = {
        field.name
        for field in fields(TerminologyMappingCandidate)
    }
    for forbidden in (
        "decision",
        "reviewer_id",
        "terminology_decision_id",
        "accepted",
        "engineering_approval",
    ):
        assert forbidden not in names


def test_creation_preserves_consensus_and_versions() -> None:
    selected = candidate()

    assert selected.project_id == PROJECT_ID
    assert selected.terminology_mapping_candidate_id == "TMC-000001"
    assert selected.mapping_status == "mapped"
    assert selected.confidence == "high"
    assert selected.confirmation_required is True
    assert selected.ontology_registry_version == "1.0.0"
    assert selected.reference_concept_index_version == "1.0.0"
    assert selected.turing_core_version == "1.0.0"
    assert selected.project_glossary_revision == 1


def test_round_trip_is_lossless_and_deterministic() -> None:
    original = candidate()
    first = terminology_mapping_candidate_to_json(original)
    second = terminology_mapping_candidate_to_json(original)

    assert first == second
    assert terminology_mapping_candidate_from_json(first) == original


def test_fingerprint_is_deterministic() -> None:
    first = candidate()
    second = candidate()

    assert first.content_fingerprint == second.content_fingerprint
    assert calculate_terminology_mapping_fingerprint(first) == (
        first.content_fingerprint
    )


def test_identity_and_timestamp_do_not_change_content_fingerprint() -> None:
    first = candidate()
    second = candidate(
        candidate_id="TMC-000002",
        timestamp="2026-07-24T16:00:00Z",
    )

    assert first.content_fingerprint == second.content_fingerprint


def test_changed_mapping_changes_fingerprint() -> None:
    original = candidate()
    changed = replace(
        original,
        mapping_status="conflict",
        review_required=True,
        recommended_review_mode="detailed_review",
    )

    assert calculate_terminology_mapping_fingerprint(changed) != (
        original.content_fingerprint
    )


def test_non_persistable_outcome_is_rejected() -> None:
    selected = consensus_outcome(persistence_eligible=False)

    with pytest.raises(TerminologyMappingIntegrityError):
        candidate(outcome=selected)


def test_outcome_must_belong_to_consensus_result() -> None:
    selected = consensus_outcome()
    other = replace(selected, confidence_rationale="Other result.")

    with pytest.raises(TerminologyMappingReferenceError):
        create_terminology_mapping_candidate(
            consensus_result=consensus_result(selected),
            outcome=other,
            terminology_mapping_candidate_id="TMC-000001",
            timestamp=TIMESTAMP,
        )


@pytest.mark.parametrize(
    "candidate_id",
    ["", "TMC-000000", "TMC-1", "TMAC-000001"],
)
def test_invalid_candidate_id_is_rejected(
    candidate_id: str,
) -> None:
    with pytest.raises(TerminologyMappingValidationError):
        candidate(candidate_id=candidate_id)


@pytest.mark.parametrize(
    ("expected_name", "expected_value"),
    [
        ("expected_project_id", "318605"),
        ("expected_information_unit_id", "IU-000002"),
        (
            "expected_terminology_mapping_candidate_id",
            "TMC-000002",
        ),
    ],
)
def test_expected_reference_mismatch_is_rejected(
    expected_name: str,
    expected_value: str,
) -> None:
    with pytest.raises(TerminologyMappingReferenceError):
        parse_terminology_mapping_candidate(
            payload(),
            **{expected_name: expected_value},
        )


@pytest.mark.parametrize(
    "field_name",
    sorted(
        {
            "schema_version",
            "project_id",
            "source_id",
            "source_projection_id",
            "information_unit_id",
            "terminology_mapping_candidate_id",
            "occurrence",
            "mapping_status",
            "proposals",
            "candidate_references",
            "team_id",
            "required_personas",
            "llm_provider",
            "llm_model",
            "prompt_schema_version",
            "ontology_registry_version",
            "reference_concept_index_version",
            "turing_core_version",
            "project_glossary_revision",
            "consensus_level",
            "variance_level",
            "confidence",
            "confidence_rationale",
            "confirmation_required",
            "review_required",
            "recommended_review_mode",
            "content_fingerprint",
            "created_at",
        }
    ),
)
def test_missing_field_is_rejected(field_name: str) -> None:
    data = payload()
    del data[field_name]

    with pytest.raises(TerminologyMappingValidationError):
        parse_terminology_mapping_candidate(data)


def test_unknown_field_is_rejected() -> None:
    data = payload()
    data["unexpected"] = True

    with pytest.raises(TerminologyMappingValidationError):
        parse_terminology_mapping_candidate(data)


def test_tampered_content_is_rejected() -> None:
    data = payload()
    data["confidence_rationale"] = "Tampered rationale."

    with pytest.raises(TerminologyMappingIntegrityError):
        parse_terminology_mapping_candidate(data)


def test_confirmation_is_always_required() -> None:
    data = payload()
    data["confirmation_required"] = False
    transient = TerminologyMappingCandidate(**data)
    data["content_fingerprint"] = (
        calculate_terminology_mapping_fingerprint(transient)
    )

    with pytest.raises(TerminologyMappingIntegrityError):
        parse_terminology_mapping_candidate(data)


@pytest.mark.parametrize(
    "status",
    ["ambiguous", "conflict"],
)
def test_ambiguous_and_conflict_require_detailed_review(
    status: str,
) -> None:
    data = payload()
    data["mapping_status"] = status
    data["review_required"] = False
    data["recommended_review_mode"] = "quick_confirmation"
    transient = TerminologyMappingCandidate(**data)
    data["content_fingerprint"] = (
        calculate_terminology_mapping_fingerprint(transient)
    )

    with pytest.raises(TerminologyMappingIntegrityError):
        parse_terminology_mapping_candidate(data)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_candidate_from_json("{invalid")


def test_duplicate_json_key_is_rejected() -> None:
    text = terminology_mapping_candidate_to_json(candidate())
    duplicate = text.replace(
        '"schema_version": "1.0.0",',
        (
            '"schema_version": "1.0.0",\n'
            '  "schema_version": "1.0.0",'
        ),
        1,
    )

    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_candidate_from_json(duplicate)


def test_validate_accepts_valid_candidate() -> None:
    assert validate_terminology_mapping_candidate(candidate()) is None


def test_serialization_rejects_wrong_type() -> None:
    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_candidate_to_dict(object())