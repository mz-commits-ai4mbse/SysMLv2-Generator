"""Tests for persistent Framework Assignment Candidate manifests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json

import pytest

from modules.framework_assignment.agent_manifest import (
    create_framework_assignment_basis,
    create_framework_assignment_proposal,
)
from modules.framework_assignment.analyzer import (
    FrameworkAssignmentConsensusResult,
)
from modules.framework_assignment.candidate_manifest import (
    FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION,
    calculate_framework_assignment_fingerprint,
    create_framework_assignment_candidate,
    framework_assignment_candidate_from_json,
    framework_assignment_candidate_to_dict,
    framework_assignment_candidate_to_json,
    parse_framework_assignment_candidate,
    validate_framework_assignment_candidate,
)
from modules.framework_assignment.errors import (
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentConsensusOutcome,
)


PROJECT_ID = "318604"
TIMESTAMP = "2026-07-24T20:00:00Z"


def proposal(node_id: str = "FW_SYSTEM_REQUIREMENTS") -> object:
    basis = create_framework_assignment_basis(
        basis_type="information_unit",
        reference_id="IU-000001",
        reference_version="a" * 64,
        rationale="Exact immutable Information Unit.",
    )
    return create_framework_assignment_proposal(
        framework_node_id=node_id,
        assignment_bases=(basis,),
        rationale="The claim belongs to this framework node.",
    )


def outcome(
    *,
    status: str = "assigned",
    proposals: tuple[object, ...] | None = None,
    confidence: str = "high",
    review_required: bool = False,
    persistence_eligible: bool = True,
    confirmation_required: bool = True,
) -> FrameworkAssignmentConsensusOutcome:
    return FrameworkAssignmentConsensusOutcome(
        information_unit_id="IU-000001",
        assignment_status=status,
        selected_proposals=(
            (proposal(),)
            if proposals is None
            else proposals
        ),
        candidate_references=(
            FrameworkAssignmentAgentCandidateReference(
                persona_id="persona-a",
                agent_id="agent-a",
                persona_run_index=1,
                framework_assignment_agent_candidate_id=(
                    "FAAC-000001"
                ),
            ),
            FrameworkAssignmentAgentCandidateReference(
                persona_id="persona-b",
                agent_id="agent-b",
                persona_run_index=1,
                framework_assignment_agent_candidate_id=(
                    "FAAC-000001"
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
        confirmation_required=confirmation_required,
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
    selected_outcome: FrameworkAssignmentConsensusOutcome | None = None,
) -> FrameworkAssignmentConsensusResult:
    selected = outcome() if selected_outcome is None else selected_outcome
    return FrameworkAssignmentConsensusResult(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
        team_id="framework-team",
        required_personas=("persona-a", "persona-b"),
        persona_run_expectations=(
            ("persona-a", 1),
            ("persona-b", 1),
        ),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=("TMC-000001",),
        outcomes=(selected,),
        issues=(),
        created_at="2026-07-24T19:00:00Z",
    )


def candidate(
    *,
    candidate_id: str = "FAC-000001",
    selected_outcome: FrameworkAssignmentConsensusOutcome
    | None = None,
    timestamp: str = TIMESTAMP,
) -> FrameworkAssignmentCandidate:
    selected = (
        outcome()
        if selected_outcome is None
        else selected_outcome
    )
    return create_framework_assignment_candidate(
        consensus_result=consensus_result(selected),
        outcome=selected,
        framework_assignment_candidate_id=candidate_id,
        timestamp=timestamp,
    )


def payload() -> dict[str, object]:
    return framework_assignment_candidate_to_dict(candidate())


def recalculate(data: dict[str, object]) -> None:
    temporary = dict(data)
    temporary["content_fingerprint"] = "0" * 64
    value = object.__new__(FrameworkAssignmentCandidate)
    parsed = None
    try:
        parsed = parse_framework_assignment_candidate(temporary)
    except FrameworkAssignmentIntegrityError:
        pass
    if parsed is not None:
        data["content_fingerprint"] = (
            calculate_framework_assignment_fingerprint(parsed)
        )
        return

    identity_free = dict(data)
    identity_free.pop("framework_assignment_candidate_id")
    identity_free.pop("content_fingerprint")
    identity_free.pop("created_at")
    canonical = json.dumps(
        identity_free,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    from hashlib import sha256

    data["content_fingerprint"] = sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def test_schema_version_is_explicit() -> None:
    assert FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION == (
        "1.0.0"
    )


def test_create_candidate_copies_consensus_context() -> None:
    selected = candidate()

    assert selected.project_id == PROJECT_ID
    assert selected.framework_assignment_candidate_id == (
        "FAC-000001"
    )
    assert selected.framework_template_id == (
        "TURING_RFLP_FRAMEWORK"
    )
    assert selected.framework_template_version == "1.0.0"
    assert selected.terminology_mapping_candidate_ids == (
        "TMC-000001",
    )
    assert selected.confirmation_required is True


def test_candidate_is_frozen_and_slotted() -> None:
    selected = candidate()

    assert selected.__dataclass_params__.frozen
    assert selected.__slots__
    with pytest.raises(FrozenInstanceError):
        selected.confidence = "low"


def test_json_round_trip_is_deterministic() -> None:
    selected = candidate()
    first = framework_assignment_candidate_to_json(selected)
    reloaded = framework_assignment_candidate_from_json(first)
    second = framework_assignment_candidate_to_json(reloaded)

    assert reloaded == selected
    assert first == second
    assert first.endswith("\n")


def test_dictionary_round_trip() -> None:
    selected = candidate()

    assert parse_framework_assignment_candidate(
        framework_assignment_candidate_to_dict(selected)
    ) == selected
    validate_framework_assignment_candidate(selected)


def test_fingerprint_is_stable() -> None:
    selected = candidate()

    assert selected.content_fingerprint == (
        calculate_framework_assignment_fingerprint(selected)
    )
    assert len(selected.content_fingerprint) == 64


def test_fingerprint_excludes_id_and_timestamp() -> None:
    first = candidate(
        candidate_id="FAC-000001",
        timestamp="2026-07-24T20:00:00Z",
    )
    second = candidate(
        candidate_id="FAC-000999",
        timestamp="2026-07-24T21:00:00Z",
    )

    assert first.content_fingerprint == second.content_fingerprint


@pytest.mark.parametrize(
    "field_name",
    (
        "assignment_status",
        "proposals",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
        "consensus_level",
        "variance_level",
        "confidence",
        "review_required",
        "recommended_review_mode",
    ),
)
def test_fingerprint_covers_professional_content(
    field_name: str,
) -> None:
    first = payload()
    second = deepcopy(first)
    replacements = {
        "assignment_status": "ambiguous",
        "proposals": [
            first["proposals"][0],
            {
                **deepcopy(first["proposals"][0]),
                "framework_node_id": "FW_SYSTEM_FUNCTIONAL",
            },
        ],
        "framework_template_version": "2.0.0",
        "turing_core_version": "2.0.0",
        "project_glossary_revision": 2,
        "terminology_mapping_candidate_ids": ["TMC-000002"],
        "consensus_level": "majority",
        "variance_level": "medium",
        "confidence": "medium",
        "review_required": True,
        "recommended_review_mode": "detailed_review",
    }
    second[field_name] = replacements[field_name]
    recalculate(second)

    assert second["content_fingerprint"] != (
        first["content_fingerprint"]
    )


def test_tampered_content_is_rejected() -> None:
    data = payload()
    data["confidence"] = "medium"

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_persistence_ineligible_outcome_is_rejected() -> None:
    selected = outcome(persistence_eligible=False)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        create_framework_assignment_candidate(
            consensus_result=consensus_result(selected),
            outcome=selected,
            framework_assignment_candidate_id="FAC-000001",
            timestamp=TIMESTAMP,
        )


def test_candidate_always_requires_confirmation() -> None:
    selected = outcome(confirmation_required=False)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        create_framework_assignment_candidate(
            consensus_result=consensus_result(selected),
            outcome=selected,
            framework_assignment_candidate_id="FAC-000001",
            timestamp=TIMESTAMP,
        )


def test_outcome_must_belong_to_consensus_result() -> None:
    first = outcome()
    other = replace(
        first,
        confidence_rationale="Different object.",
    )

    with pytest.raises(FrameworkAssignmentReferenceError):
        create_framework_assignment_candidate(
            consensus_result=consensus_result(first),
            outcome=other,
            framework_assignment_candidate_id="FAC-000001",
            timestamp=TIMESTAMP,
        )


def test_wrong_creation_types_are_rejected() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        create_framework_assignment_candidate(
            consensus_result=object(),
            outcome=outcome(),
            framework_assignment_candidate_id="FAC-000001",
            timestamp=TIMESTAMP,
        )
    with pytest.raises(FrameworkAssignmentValidationError):
        create_framework_assignment_candidate(
            consensus_result=consensus_result(),
            outcome=object(),
            framework_assignment_candidate_id="FAC-000001",
            timestamp=TIMESTAMP,
        )


def test_expected_identifiers_are_enforced() -> None:
    data = payload()

    with pytest.raises(FrameworkAssignmentReferenceError):
        parse_framework_assignment_candidate(
            data,
            expected_project_id="999999",
        )
    with pytest.raises(FrameworkAssignmentReferenceError):
        parse_framework_assignment_candidate(
            data,
            expected_information_unit_id="IU-000002",
        )
    with pytest.raises(FrameworkAssignmentReferenceError):
        parse_framework_assignment_candidate(
            data,
            expected_framework_assignment_candidate_id=(
                "FAC-000002"
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("schema_version", "2.0.0"),
        ("project_id", ""),
        ("source_id", []),
        ("source_projection_id", " bad"),
        ("information_unit_id", "IU-00001"),
        ("framework_assignment_candidate_id", "FAC-000000"),
        ("assignment_status", "approved"),
        ("proposals", {}),
        ("candidate_references", []),
        ("team_id", "team id"),
        ("required_personas", []),
        ("llm_provider", ""),
        ("llm_model", None),
        ("prompt_schema_version", "1.0"),
        ("framework_template_id", "lower"),
        ("framework_template_version", "v1"),
        ("turing_core_version", "1"),
        ("project_glossary_revision", 0),
        ("terminology_mapping_candidate_ids", "TMC-000001"),
        ("consensus_level", "unknown"),
        ("variance_level", "unknown"),
        ("confidence", "unknown"),
        ("confidence_rationale", ""),
        ("confirmation_required", False),
        ("review_required", "false"),
        ("recommended_review_mode", "unknown"),
        ("content_fingerprint", "a"),
        ("created_at", "2026-07-24"),
    ),
)
def test_invalid_fields_are_rejected(
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
        parse_framework_assignment_candidate(data)


def test_review_flag_and_mode_must_agree() -> None:
    data = payload()
    data["review_required"] = True
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_status_and_proposals_must_agree() -> None:
    data = payload()
    data["assignment_status"] = "unassigned"
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_duplicate_node_proposals_are_rejected() -> None:
    data = payload()
    data["proposals"].append(deepcopy(data["proposals"][0]))
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_duplicate_candidate_references_are_rejected() -> None:
    data = payload()
    data["candidate_references"].append(
        deepcopy(data["candidate_references"][0])
    )
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_duplicate_personas_are_rejected() -> None:
    data = payload()
    data["required_personas"] = ["persona-a", "persona-a"]
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_duplicate_terminology_ids_are_rejected() -> None:
    data = payload()
    data["terminology_mapping_candidate_ids"] = [
        "TMC-000001",
        "TMC-000001",
    ]
    recalculate(data)

    with pytest.raises(FrameworkAssignmentIntegrityError):
        parse_framework_assignment_candidate(data)


def test_unknown_and_missing_fields_are_rejected() -> None:
    unknown = payload()
    unknown["accepted"] = True
    missing = payload()
    del missing["confirmation_required"]

    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_candidate(unknown)
    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_candidate(missing)


def test_nested_unknown_fields_are_rejected() -> None:
    data = payload()
    data["proposals"][0]["unexpected"] = True

    with pytest.raises(FrameworkAssignmentValidationError):
        parse_framework_assignment_candidate(data)


def test_duplicate_json_keys_are_rejected() -> None:
    text = framework_assignment_candidate_to_json(candidate())
    duplicated = text.replace(
        '"schema_version": "1.0.0",',
        (
            '"schema_version": "1.0.0",\n'
            '  "schema_version": "1.0.0",'
        ),
        1,
    )

    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_candidate_from_json(duplicated)


@pytest.mark.parametrize(
    "text",
    (
        "{invalid",
        "[]",
        "null",
        "42",
    ),
)
def test_invalid_json_is_rejected(text: str) -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_candidate_from_json(text)


def test_non_string_json_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_candidate_from_json(42)


def test_serialization_rejects_wrong_type() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        framework_assignment_candidate_to_dict(object())