"""Tests for deterministic framework-assignment consensus."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from modules.framework_assignment.agent_manifest import (
    create_framework_assignment_agent_candidate,
    create_framework_assignment_agent_result,
    create_framework_assignment_basis,
    create_framework_assignment_proposal,
)
from modules.framework_assignment.analyzer import (
    FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION,
    FRAMEWORK_ASSIGNMENT_SIGNATURE_ID,
    FRAMEWORK_ASSIGNMENT_SIGNATURE_VERSION,
    FrameworkAssignmentConsensusResult,
    analyze_framework_assignment_consensus,
    framework_assignment_signature,
)
from modules.framework_assignment.errors import (
    DuplicateFrameworkAssignmentAgentResultError,
    FrameworkAssignmentComparisonError,
    FrameworkAssignmentConfigurationError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentAgentCandidate,
)
from modules.information_units.types import InformationUnit


PROJECT_ID = "318604"
FINGERPRINT = "a" * 64
TIMESTAMP = "2026-07-24T19:00:00Z"


def information_unit() -> InformationUnit:
    value = object.__new__(InformationUnit)
    for name, field_value in {
        "project_id": PROJECT_ID,
        "source_id": "SRC-000001",
        "source_projection_id": "SP-000001",
        "information_unit_id": "IU-000001",
        "content_fingerprint": FINGERPRINT,
    }.items():
        object.__setattr__(value, name, field_value)
    return value


def proposal(node_id: str) -> object:
    basis = create_framework_assignment_basis(
        basis_type="information_unit",
        reference_id="IU-000001",
        reference_version=FINGERPRINT,
        rationale="Exact immutable Information Unit.",
    )
    return create_framework_assignment_proposal(
        framework_node_id=node_id,
        assignment_bases=(basis,),
        rationale=f"Assign to {node_id}.",
    )


def candidate(
    *,
    candidate_id: str = "FAAC-000001",
    nodes: tuple[str, ...] = ("FW_SYSTEM_REQUIREMENTS",),
    status: str = "assigned",
    rationale: str = "Persona classification.",
) -> FrameworkAssignmentAgentCandidate:
    return create_framework_assignment_agent_candidate(
        framework_assignment_agent_candidate_id=candidate_id,
        information_unit_id="IU-000001",
        assignment_status=status,
        proposals=tuple(proposal(node) for node in nodes),
        rationale=rationale,
        uncertainties=(),
    )


def result(
    *,
    persona_id: str,
    run_index: int = 1,
    nodes: tuple[str, ...] = ("FW_SYSTEM_REQUIREMENTS",),
    status: str = "assigned",
    rationale: str = "Persona classification.",
    no_candidate: bool = False,
    agent_id: str | None = None,
) -> object:
    selected_candidates = (
        ()
        if no_candidate
        else (
            candidate(
                candidate_id=f"FAAC-{run_index:06d}",
                nodes=nodes,
                status=status,
                rationale=rationale,
            ),
        )
    )
    return create_framework_assignment_agent_result(
        information_unit=information_unit(),
        team_id="framework-team",
        agent_id=agent_id or f"agent-{persona_id}",
        persona_id=persona_id,
        persona_run_index=run_index,
        persona_configuration_fingerprint="b" * 64,
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=("TMC-000001",),
        candidates=selected_candidates,
        no_candidate_rationale=(
            "No defensible assignment."
            if no_candidate
            else None
        ),
        timestamp=TIMESTAMP,
    )


def analyze(
    results: tuple[object, ...],
    *,
    personas: tuple[str, ...] = ("persona-a", "persona-b"),
    runs: dict[str, int] | None = None,
) -> FrameworkAssignmentConsensusResult:
    return analyze_framework_assignment_consensus(
        agent_results=results,
        required_personas=personas,
        expected_runs_per_persona=(
            {persona: 1 for persona in personas}
            if runs is None
            else runs
        ),
        information_unit=information_unit(),
        timestamp=TIMESTAMP,
    )


def test_consensus_metadata_is_explicit() -> None:
    assert FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION == (
        "1.0.0"
    )
    assert FRAMEWORK_ASSIGNMENT_SIGNATURE_ID == (
        "assignment_status_and_framework_node_set"
    )
    assert FRAMEWORK_ASSIGNMENT_SIGNATURE_VERSION == "1.0.0"


def test_unanimous_personas_produce_high_confidence() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(persona_id="persona-b"),
        )
    )
    outcome = consensus.outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.variance_level == "low"
    assert outcome.confidence == "high"
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )
    assert outcome.dissenting_personas == ()
    assert outcome.omitting_personas == ()
    assert outcome.confirmation_required is True
    assert outcome.review_required is False
    assert outcome.recommended_review_mode == (
        "quick_confirmation"
    )
    assert outcome.persistence_eligible is True


def test_result_is_frozen_and_slotted() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(persona_id="persona-b"),
        )
    )

    assert consensus.__dataclass_params__.frozen
    assert consensus.__slots__
    with pytest.raises(FrozenInstanceError):
        consensus.team_id = "other"


def test_rationale_differences_are_not_professional_dissent() -> None:
    consensus = analyze(
        (
            result(
                persona_id="persona-a",
                rationale="Reason A.",
            ),
            result(
                persona_id="persona-b",
                rationale="Different wording.",
            ),
        )
    )

    assert consensus.outcomes[0].confidence == "high"
    assert (
        len(consensus.outcomes[0].value_distribution)
        == 1
    )


def test_node_order_does_not_change_signature() -> None:
    first = candidate(
        nodes=(
            "FW_SYSTEM_REQUIREMENTS",
            "FW_SYSTEM_FUNCTIONAL",
        )
    )
    second = candidate(
        nodes=(
            "FW_SYSTEM_FUNCTIONAL",
            "FW_SYSTEM_REQUIREMENTS",
        )
    )

    assert framework_assignment_signature(first) == (
        framework_assignment_signature(second)
    )


def test_status_changes_signature() -> None:
    assigned = candidate()
    ambiguous = candidate(
        status="ambiguous",
        nodes=(
            "FW_SYSTEM_REQUIREMENTS",
            "FW_STAKEHOLDER_REQUIREMENTS",
        ),
    )

    assert framework_assignment_signature(assigned) != (
        framework_assignment_signature(ambiguous)
    )


def test_signature_rejects_wrong_type() -> None:
    with pytest.raises(FrameworkAssignmentComparisonError):
        framework_assignment_signature(object())


def test_unanimous_multiple_assignments_remain_multiple() -> None:
    nodes = (
        "FW_SYSTEM_REQUIREMENTS",
        "FW_SYSTEM_FUNCTIONAL",
    )
    consensus = analyze(
        (
            result(persona_id="persona-a", nodes=nodes),
            result(
                persona_id="persona-b",
                nodes=tuple(reversed(nodes)),
            ),
        )
    )

    assert consensus.outcomes[0].assignment_status == "assigned"
    assert {
        item.framework_node_id
        for item in consensus.outcomes[0].selected_proposals
    } == set(nodes)
    assert consensus.outcomes[0].confidence == "high"


def test_majority_produces_medium_confidence() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(persona_id="persona-b"),
            result(
                persona_id="persona-c",
                nodes=("FW_SYSTEM_FUNCTIONAL",),
            ),
        ),
        personas=("persona-a", "persona-b", "persona-c"),
    )
    outcome = consensus.outcomes[0]

    assert outcome.consensus_level == "majority"
    assert outcome.variance_level == "medium"
    assert outcome.confidence == "medium"
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )
    assert outcome.dissenting_personas == ("persona-c",)
    assert outcome.review_required is True
    assert outcome.recommended_review_mode == "detailed_review"


def test_tied_personas_are_incomparable() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(
                persona_id="persona-b",
                nodes=("FW_SYSTEM_FUNCTIONAL",),
            ),
        )
    )
    outcome = consensus.outcomes[0]

    assert outcome.consensus_level == "incomparable"
    assert outcome.confidence == "low"
    assert outcome.selected_proposals == ()
    assert outcome.persistence_eligible is False
    assert outcome.review_required is True


def test_missing_required_persona_is_incomplete() -> None:
    consensus = analyze(
        (result(persona_id="persona-a"),)
    )
    outcome = consensus.outcomes[0]

    assert outcome.consensus_level == "incomplete"
    assert outcome.confidence == "low"
    assert outcome.omitting_personas == ("persona-b",)
    assert any(
        issue.code == "missing_persona_runs"
        for issue in consensus.issues
    )


def test_one_persona_no_candidate_is_incomplete() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(
                persona_id="persona-b",
                no_candidate=True,
            ),
        )
    )

    assert consensus.outcomes[0].consensus_level == "incomplete"
    assert consensus.outcomes[0].omitting_personas == (
        "persona-b",
    )


def test_all_personas_no_candidate_produce_issue_only() -> None:
    consensus = analyze(
        (
            result(
                persona_id="persona-a",
                no_candidate=True,
            ),
            result(
                persona_id="persona-b",
                no_candidate=True,
            ),
        )
    )

    assert consensus.outcomes == ()
    assert any(
        issue.code == "no_framework_assignment_candidates"
        for issue in consensus.issues
    )


def test_unanimous_explicit_unassigned_is_valid_candidate() -> None:
    consensus = analyze(
        (
            result(
                persona_id="persona-a",
                status="unassigned",
                nodes=(),
            ),
            result(
                persona_id="persona-b",
                status="unassigned",
                nodes=(),
            ),
        )
    )
    outcome = consensus.outcomes[0]

    assert outcome.assignment_status == "unassigned"
    assert outcome.confidence == "high"
    assert outcome.persistence_eligible is True


@pytest.mark.parametrize(
    "status",
    (
        "ambiguous",
        "conflict",
    ),
)
def test_unanimous_detailed_status_still_requires_review(
    status: str,
) -> None:
    nodes = (
        "FW_SYSTEM_REQUIREMENTS",
        "FW_STAKEHOLDER_REQUIREMENTS",
    )
    consensus = analyze(
        (
            result(
                persona_id="persona-a",
                status=status,
                nodes=nodes,
            ),
            result(
                persona_id="persona-b",
                status=status,
                nodes=nodes,
            ),
        )
    )
    outcome = consensus.outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.review_required is True
    assert outcome.recommended_review_mode == "detailed_review"
    assert status in outcome.confidence_rationale


def test_repeated_run_instability_caps_confidence() -> None:
    results = (
        result(persona_id="persona-a", run_index=1),
        result(persona_id="persona-a", run_index=2),
        result(
            persona_id="persona-a",
            run_index=3,
            nodes=("FW_SYSTEM_FUNCTIONAL",),
        ),
        result(persona_id="persona-b", run_index=1),
        result(persona_id="persona-b", run_index=2),
        result(persona_id="persona-b", run_index=3),
    )
    consensus = analyze(
        results,
        runs={"persona-a": 3, "persona-b": 3},
    )
    outcome = consensus.outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.confidence == "medium"
    assert outcome.review_required is True
    assert any(
        issue.code == "unstable_persona_assignment"
        for issue in consensus.issues
    )


def test_repeated_run_tie_is_indeterminate() -> None:
    results = (
        result(persona_id="persona-a", run_index=1),
        result(
            persona_id="persona-a",
            run_index=2,
            nodes=("FW_SYSTEM_FUNCTIONAL",),
        ),
        result(persona_id="persona-b", run_index=1),
        result(persona_id="persona-b", run_index=2),
    )
    consensus = analyze(
        results,
        runs={"persona-a": 2, "persona-b": 2},
    )

    assert consensus.outcomes[0].consensus_level == "incomplete"
    assert any(
        issue.code == "indeterminate_persona_assignment"
        for issue in consensus.issues
    )


def test_repeated_candidate_omission_can_be_unstable() -> None:
    results = (
        result(persona_id="persona-a", run_index=1),
        result(persona_id="persona-a", run_index=2),
        result(
            persona_id="persona-a",
            run_index=3,
            no_candidate=True,
        ),
        result(persona_id="persona-b", run_index=1),
        result(persona_id="persona-b", run_index=2),
        result(persona_id="persona-b", run_index=3),
    )
    consensus = analyze(
        results,
        runs={"persona-a": 3, "persona-b": 3},
    )

    assert consensus.outcomes[0].confidence == "medium"
    assert any(
        issue.code == "unstable_persona_assignment"
        for issue in consensus.issues
    )


def test_value_distribution_is_deterministic() -> None:
    results = (
        result(persona_id="persona-b"),
        result(persona_id="persona-a"),
        result(
            persona_id="persona-c",
            nodes=("FW_SYSTEM_FUNCTIONAL",),
        ),
    )
    first = analyze(
        results,
        personas=("persona-a", "persona-b", "persona-c"),
    )
    second = analyze(
        tuple(reversed(results)),
        personas=("persona-a", "persona-b", "persona-c"),
    )

    assert first == second


def test_candidate_references_preserve_persona_runs() -> None:
    consensus = analyze(
        (
            result(persona_id="persona-a"),
            result(persona_id="persona-b"),
        )
    )
    references = consensus.outcomes[0].candidate_references

    assert tuple(
        reference.persona_id
        for reference in references
    ) == ("persona-a", "persona-b")
    assert all(
        reference.framework_assignment_agent_candidate_id
        == "FAAC-000001"
        for reference in references
    )


@pytest.mark.parametrize(
    "field_name",
    (
        "project_id",
        "source_id",
        "source_projection_id",
        "team_id",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "framework_template_id",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
    ),
)
def test_inconsistent_result_configuration_is_rejected(
    field_name: str,
) -> None:
    first = result(persona_id="persona-a")
    current = getattr(first, field_name)
    replacement = {
        "project_id": "999999",
        "source_id": "SRC-000002",
        "source_projection_id": "SP-000002",
        "information_unit_id": "IU-000002",
        "team_id": "other-team",
        "llm_provider": "other-provider",
        "llm_model": "other-model",
        "prompt_schema_version": "2.0.0",
        "framework_template_id": "OTHER_FRAMEWORK",
        "framework_template_version": "2.0.0",
        "turing_core_version": "2.0.0",
        "project_glossary_revision": 2,
        "terminology_mapping_candidate_ids": ("TMC-000002",),
    }[field_name]
    second = replace(
        result(persona_id="persona-b"),
        **{field_name: replacement},
    )

    with pytest.raises(FrameworkAssignmentConfigurationError):
        analyze((first, second))


def test_result_information_unit_mismatch_is_rejected() -> None:
    mismatched = replace(
        result(persona_id="persona-a"),
        information_unit_id="IU-000002",
    )

    with pytest.raises(FrameworkAssignmentReferenceError):
        analyze(
            (
                mismatched,
                result(persona_id="persona-b"),
            )
        )


def test_duplicate_persona_run_is_rejected() -> None:
    with pytest.raises(
        DuplicateFrameworkAssignmentAgentResultError
    ):
        analyze(
            (
                result(
                    persona_id="persona-a",
                    agent_id="agent-one",
                ),
                result(
                    persona_id="persona-a",
                    agent_id="agent-two",
                ),
            ),
            personas=("persona-a",),
        )


@pytest.mark.parametrize(
    "results",
    (
        (),
        "not-results",
        (object(),),
    ),
)
def test_invalid_agent_result_collections_are_rejected(
    results: object,
) -> None:
    with pytest.raises(
        (
            FrameworkAssignmentValidationError,
            FrameworkAssignmentConfigurationError,
        )
    ):
        analyze_framework_assignment_consensus(
            agent_results=results,
            required_personas=("persona-a",),
            expected_runs_per_persona={"persona-a": 1},
            information_unit=information_unit(),
            timestamp=TIMESTAMP,
        )


@pytest.mark.parametrize(
    "personas",
    (
        (),
        "persona-a",
        ("persona-a", "persona-a"),
        ("",),
        (" persona-a",),
    ),
)
def test_invalid_required_personas_are_rejected(
    personas: object,
) -> None:
    with pytest.raises(FrameworkAssignmentConfigurationError):
        analyze_framework_assignment_consensus(
            agent_results=(result(persona_id="persona-a"),),
            required_personas=personas,
            expected_runs_per_persona={"persona-a": 1},
            information_unit=information_unit(),
            timestamp=TIMESTAMP,
        )


@pytest.mark.parametrize(
    "expectations",
    (
        {},
        {"persona-a": 1, "persona-b": 1},
        {"persona-a": 0},
        {"persona-a": True},
        {"persona-a": "1"},
        [],
    ),
)
def test_invalid_run_expectations_are_rejected(
    expectations: object,
) -> None:
    with pytest.raises(FrameworkAssignmentConfigurationError):
        analyze_framework_assignment_consensus(
            agent_results=(result(persona_id="persona-a"),),
            required_personas=("persona-a",),
            expected_runs_per_persona=expectations,
            information_unit=information_unit(),
            timestamp=TIMESTAMP,
        )


def test_unexpected_persona_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentConfigurationError):
        analyze(
            (result(persona_id="persona-c"),)
        )


def test_run_index_above_expectation_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentConfigurationError):
        analyze(
            (
                result(
                    persona_id="persona-a",
                    run_index=2,
                ),
            ),
            personas=("persona-a",),
        )


@pytest.mark.parametrize(
    "timestamp",
    (
        "",
        "2026-07-24",
        " 2026-07-24T19:00:00Z",
        "2026-07-24T19:00:00+00:00",
        None,
    ),
)
def test_invalid_timestamps_are_rejected(
    timestamp: object,
) -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        analyze_framework_assignment_consensus(
            agent_results=(result(persona_id="persona-a"),),
            required_personas=("persona-a",),
            expected_runs_per_persona={"persona-a": 1},
            information_unit=information_unit(),
            timestamp=timestamp,
        )


def test_non_information_unit_is_rejected() -> None:
    with pytest.raises(FrameworkAssignmentValidationError):
        analyze_framework_assignment_consensus(
            agent_results=(result(persona_id="persona-a"),),
            required_personas=("persona-a",),
            expected_runs_per_persona={"persona-a": 1},
            information_unit=object(),
            timestamp=TIMESTAMP,
        )