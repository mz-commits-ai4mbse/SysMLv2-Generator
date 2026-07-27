"""Tests for deterministic Preliminary Model and SubModel support."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.project_coverage.errors import (
    CoverageIntegrityError,
    CoverageProfileError,
    CoverageReferenceError,
    CoverageValidationError,
)
from modules.project_coverage.profile import (
    calculate_preliminary_support_profile_fingerprint,
    preliminary_support_profile_from_json,
)
from modules.project_coverage.support import (
    PRELIMINARY_SUPPORT_ALGORITHM_ID,
    PRELIMINARY_SUPPORT_ALGORITHM_VERSION,
    derive_potential_support_assessments,
    potential_support_by_id,
)
from modules.project_coverage.types import (
    CoverageIssue,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    PreliminarySupportProfile,
    PreliminarySupportTarget,
)


PROJECT_ID = "318604"
STAKEHOLDER_NODES = (
    "FW_STAKEHOLDER_STAKEHOLDERS",
    "FW_STAKEHOLDER_USER_NEEDS",
    "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS",
    "FW_STAKEHOLDER_USE_CASES",
)
SYSTEM_NODES = (
    "FW_SYSTEM_REQUIREMENTS",
    "FW_SYSTEM_FUNCTIONAL",
    "FW_SYSTEM_LOGICAL",
    "FW_SYSTEM_PHYSICAL",
)
SUBSYSTEM_NODES = (
    "FW_SUBSYSTEM_REQUIREMENTS",
    "FW_SUBSYSTEM_FUNCTIONAL",
    "FW_SUBSYSTEM_LOGICAL",
    "FW_SUBSYSTEM_PHYSICAL",
)
ALL_NODES = STAKEHOLDER_NODES + SYSTEM_NODES + SUBSYSTEM_NODES
TARGET_IDS = (
    "SUPPORT_STAKEHOLDER_MODEL",
    "SUPPORT_SYSTEM_MODEL",
    "SUPPORT_SUBSYSTEM_MODEL",
)


def framework_template() -> dict[str, object]:
    nodes = []
    for order, (level_id, level_name, node_ids) in enumerate(
        (
            ("FW_LEVEL_STAKEHOLDER", "Stakeholder Level", STAKEHOLDER_NODES),
            ("FW_LEVEL_SYSTEM", "System Level", SYSTEM_NODES),
            ("FW_LEVEL_SUBSYSTEM", "Subsystem Level", SUBSYSTEM_NODES),
        ),
        start=1,
    ):
        nodes.append(
            {
                "node_id": level_id,
                "mapping_key": level_id.lower(),
                "name": level_name,
                "node_type": "level",
                "parent_node_id": None,
                "mapping_target": False,
                "order": order,
            }
        )
        for child_order, node_id in enumerate(node_ids, start=1):
            nodes.append(
                {
                    "node_id": node_id,
                    "mapping_key": node_id.lower(),
                    "name": node_id,
                    "node_type": "framework_node",
                    "parent_node_id": level_id,
                    "mapping_target": True,
                    "order": child_order,
                }
            )
    return {
        "schema_version": "1.0.0",
        "template_id": "TURING_RFLP_FRAMEWORK",
        "template_version": "1.0.0",
        "name": "Turing Framework",
        "status": "active",
        "authority": {
            "definition_basis": "P6 test fixture",
            "engineering_authority": "CATIA test authority",
            "shadow_model_rule": "Test fixture does not override CATIA.",
            "non_normative_references": [],
        },
        "information_unit_mapping": {
            "eligible_source_roles": ["engineering_source"],
            "cardinality_per_information_unit": "zero_to_many",
            "target_reference_field": "node_id",
            "unknown_target_behavior": "reject",
            "context_only_mapping_allowed": False,
        },
        "assessment_semantics": {
            "preliminary_coverage": {
                "label": "Preliminary Coverage",
                "eligible_source_roles": ["engineering_source"],
                "requires_human_approval": False,
                "phase_p_available": True,
                "excluded_source_roles": ["context_only"],
            },
            "approved_readiness": {
                "label": "Approved Generation Readiness",
                "eligible_source_roles": ["engineering_source"],
                "requires_human_approval": True,
                "phase_p_available": False,
                "available_from_phase": "G",
                "excluded_source_roles": ["context_only"],
            },
        },
        "nodes": nodes,
    }


def support_profile() -> PreliminarySupportProfile:
    path = Path("context/frameworks/turing_preliminary_support_profile.json")
    return preliminary_support_profile_from_json(
        path.read_text(encoding="utf-8"),
        framework_template=framework_template(),
    )


def node_coverage(
    node_id: str,
    *,
    state: str = "uncovered",
    attention: bool = False,
    issue_codes: tuple[str, ...] = (),
) -> FrameworkNodeCoverage:
    suffix = f"{ALL_NODES.index(node_id) + 1:06d}"
    covered = state != "uncovered"
    confirmed = state == "reviewed_candidate_covered"
    unreviewed = state == "candidate_covered"
    return FrameworkNodeCoverage(
        framework_node_id=node_id,
        mapping_key=node_id.lower(),
        node_name=node_id,
        level_node_id=(
            "FW_LEVEL_STAKEHOLDER"
            if node_id in STAKEHOLDER_NODES
            else "FW_LEVEL_SYSTEM"
            if node_id in SYSTEM_NODES
            else "FW_LEVEL_SUBSYSTEM"
        ),
        coverage_state=state,
        attention_required=attention,
        eligible_source_count=1 if covered else 0,
        information_unit_count=1 if covered else 0,
        assignment_candidate_count=1 if covered else 0,
        confirmed_candidate_count=1 if confirmed else 0,
        unreviewed_candidate_count=1 if unreviewed else 0,
        rejected_candidate_count=0,
        ambiguous_candidate_count=0,
        conflicting_candidate_count=0,
        source_ids=("SRC-000001",) if covered else (),
        information_unit_ids=(f"IU-{suffix}",) if covered else (),
        framework_assignment_candidate_ids=(f"FAC-{suffix}",) if covered else (),
        human_review_decision_ids=(f"HRD-{suffix}",) if confirmed else (),
        issue_codes=issue_codes,
    )


def coverages(
    *,
    covered_nodes: tuple[str, ...] = (),
    reviewed_nodes: tuple[str, ...] = (),
    attention_nodes: tuple[str, ...] = (),
    reverse: bool = False,
) -> tuple[FrameworkNodeCoverage, ...]:
    values = []
    for node_id in ALL_NODES:
        state = (
            "reviewed_candidate_covered"
            if node_id in reviewed_nodes
            else "candidate_covered"
            if node_id in covered_nodes
            else "uncovered"
        )
        values.append(
            node_coverage(
                node_id,
                state=state,
                attention=node_id in attention_nodes,
            )
        )
    if reverse:
        values.reverse()
    return tuple(values)


def issue(
    code: str = "test_issue",
    *,
    level: str = "warning",
    node_id: str | None = None,
    target_id: str | None = None,
    project_id: str = PROJECT_ID,
) -> CoverageIssue:
    return CoverageIssue(
        project_id=project_id,
        code=code,
        message=code,
        issue_level=level,
        framework_node_id=node_id,
        support_target_id=target_id,
    )


def assess(
    selected_coverages: tuple[FrameworkNodeCoverage, ...],
    *,
    issues: tuple[CoverageIssue, ...] = (),
    profile: PreliminarySupportProfile | None = None,
) -> tuple[PotentialSupportAssessment, ...]:
    return derive_potential_support_assessments(
        PROJECT_ID,
        support_profile() if profile is None else profile,
        selected_coverages,
        issues,
    )


def states(
    assessments: tuple[PotentialSupportAssessment, ...],
) -> tuple[str, ...]:
    return tuple(item.support_state for item in assessments)


def test_algorithm_metadata() -> None:
    assert PRELIMINARY_SUPPORT_ALGORITHM_ID == "TURING_PRELIMINARY_MODEL_SUPPORT"
    assert PRELIMINARY_SUPPORT_ALGORITHM_VERSION == "1.0.0"


def test_no_coverage_supports_nothing() -> None:
    result = assess(coverages())
    assert states(result) == (
        "not_supported",
        "not_supported",
        "not_supported",
    )


def test_partial_stakeholder_is_partial_only() -> None:
    result = assess(coverages(covered_nodes=(STAKEHOLDER_NODES[0],)))
    assert states(result) == (
        "partially_supported",
        "not_supported",
        "not_supported",
    )


def test_full_stakeholder_supports_stakeholder_and_partially_system() -> None:
    result = assess(coverages(covered_nodes=STAKEHOLDER_NODES))
    assert states(result) == (
        "potentially_supported",
        "partially_supported",
        "not_supported",
    )


def test_full_stakeholder_and_partial_system() -> None:
    result = assess(
        coverages(covered_nodes=STAKEHOLDER_NODES + SYSTEM_NODES[:2])
    )
    assert states(result) == (
        "potentially_supported",
        "partially_supported",
        "not_supported",
    )


def test_full_stakeholder_and_system_supports_system() -> None:
    result = assess(
        coverages(covered_nodes=STAKEHOLDER_NODES + SYSTEM_NODES)
    )
    assert states(result) == (
        "potentially_supported",
        "potentially_supported",
        "partially_supported",
    )


def test_complete_chain_is_potentially_supported() -> None:
    result = assess(coverages(covered_nodes=ALL_NODES))
    assert states(result) == (
        "potentially_supported",
        "potentially_supported",
        "potentially_supported",
    )


def test_reviewed_and_unreviewed_coverage_are_equivalent_for_support() -> None:
    result = assess(coverages(reviewed_nodes=ALL_NODES))
    assert states(result) == (
        "potentially_supported",
        "potentially_supported",
        "potentially_supported",
    )


def test_target_order_follows_profile() -> None:
    result = assess(coverages())
    assert tuple(item.support_target_id for item in result) == TARGET_IDS


def test_required_node_order_is_preserved() -> None:
    result = assess(coverages(covered_nodes=STAKEHOLDER_NODES[:2]))
    stakeholder = result[0]
    assert stakeholder.required_framework_node_ids == STAKEHOLDER_NODES
    assert stakeholder.covered_framework_node_ids == STAKEHOLDER_NODES[:2]
    assert stakeholder.missing_framework_node_ids == STAKEHOLDER_NODES[2:]


def test_dependency_sets_are_reported() -> None:
    result = assess(coverages(covered_nodes=STAKEHOLDER_NODES))
    system = result[1]
    assert system.required_support_target_ids == (
        "SUPPORT_STAKEHOLDER_MODEL",
    )
    assert system.satisfied_support_target_ids == (
        "SUPPORT_STAKEHOLDER_MODEL",
    )
    assert system.unsatisfied_support_target_ids == ()


def test_unsatisfied_dependency_is_reported() -> None:
    result = assess(coverages(covered_nodes=SYSTEM_NODES))
    system = result[1]
    assert system.support_state == "partially_supported"
    assert system.satisfied_support_target_ids == ()
    assert system.unsatisfied_support_target_ids == (
        "SUPPORT_STAKEHOLDER_MODEL",
    )
    assert "required_support_target_unsatisfied" in system.issue_codes


def test_missing_node_code_is_reported() -> None:
    result = assess(coverages(covered_nodes=STAKEHOLDER_NODES[:3]))
    assert "required_framework_node_uncovered" in result[0].issue_codes


def test_node_issue_codes_propagate() -> None:
    selected = list(coverages(covered_nodes=STAKEHOLDER_NODES))
    selected[0] = replace(selected[0], issue_codes=("node_warning",))
    result = assess(tuple(selected))
    assert "node_warning" in result[0].issue_codes


def test_attention_on_complete_target_changes_state() -> None:
    result = assess(
        coverages(
            covered_nodes=STAKEHOLDER_NODES,
            attention_nodes=(STAKEHOLDER_NODES[0],),
        )
    )
    assert result[0].support_state == "attention_required"
    assert result[0].attention_required is True
    assert "required_framework_node_attention_required" in result[0].issue_codes


def test_upstream_attention_prevents_downstream_support() -> None:
    result = assess(
        coverages(
            covered_nodes=STAKEHOLDER_NODES + SYSTEM_NODES,
            attention_nodes=(STAKEHOLDER_NODES[0],),
        )
    )
    assert states(result)[:2] == (
        "attention_required",
        "partially_supported",
    )
    assert result[1].attention_required is True
    assert "required_support_target_attention_required" in result[1].issue_codes


def test_warning_does_not_suppress_potential_support() -> None:
    result = assess(
        coverages(covered_nodes=ALL_NODES),
        issues=(issue("warning", level="warning"),),
    )
    assert states(result) == (
        "potentially_supported",
        "potentially_supported",
        "potentially_supported",
    )
    assert all(item.attention_required for item in result)


def test_blocking_global_issue_requires_attention_when_otherwise_supported() -> None:
    result = assess(
        coverages(covered_nodes=ALL_NODES),
        issues=(issue("blocking", level="blocking"),),
    )
    assert states(result) == (
        "attention_required",
        "partially_supported",
        "partially_supported",
    )


def test_target_specific_issue_applies_only_to_target_then_propagates() -> None:
    result = assess(
        coverages(covered_nodes=ALL_NODES),
        issues=(
            issue(
                "system_blocked",
                level="blocking",
                target_id="SUPPORT_SYSTEM_MODEL",
            ),
        ),
    )
    assert states(result) == (
        "potentially_supported",
        "attention_required",
        "partially_supported",
    )
    assert "system_blocked" not in result[0].issue_codes
    assert "system_blocked" in result[1].issue_codes
    assert "system_blocked" in result[2].issue_codes


def test_node_specific_issue_applies_to_own_target() -> None:
    result = assess(
        coverages(covered_nodes=ALL_NODES),
        issues=(
            issue(
                "system_node_blocked",
                level="blocking",
                node_id=SYSTEM_NODES[0],
            ),
        ),
    )
    assert result[0].support_state == "potentially_supported"
    assert result[1].support_state == "attention_required"


def test_input_order_does_not_change_result() -> None:
    forward = assess(coverages(covered_nodes=ALL_NODES))
    reverse = assess(coverages(covered_nodes=ALL_NODES, reverse=True))
    assert forward == reverse


def test_issue_order_does_not_change_result() -> None:
    first = issue("a", target_id="SUPPORT_STAKEHOLDER_MODEL")
    second = issue("b", node_id=STAKEHOLDER_NODES[0])
    a = assess(coverages(covered_nodes=ALL_NODES), issues=(first, second))
    b = assess(coverages(covered_nodes=ALL_NODES), issues=(second, first))
    assert a == b


def test_issue_codes_are_sorted_and_unique() -> None:
    selected = list(coverages(covered_nodes=STAKEHOLDER_NODES))
    selected[0] = replace(selected[0], issue_codes=("z", "a"))
    result = assess(
        tuple(selected),
        issues=(issue("m", target_id="SUPPORT_STAKEHOLDER_MODEL"),),
    )
    assert result[0].issue_codes == tuple(sorted(set(result[0].issue_codes)))


def test_lookup_returns_exact_assessment() -> None:
    result = assess(coverages())
    assert potential_support_by_id(
        result,
        "SUPPORT_SYSTEM_MODEL",
    ) == result[1]


def test_lookup_rejects_unknown_target() -> None:
    with pytest.raises(CoverageReferenceError):
        potential_support_by_id(assess(coverages()), "SUPPORT_UNKNOWN")


def test_lookup_rejects_duplicate_assessments() -> None:
    result = assess(coverages())
    with pytest.raises(CoverageIntegrityError):
        potential_support_by_id((result[0], result[0]), TARGET_IDS[0])


@pytest.mark.parametrize("value", [None, "", "   ", 123])
def test_invalid_project_id_is_rejected(value) -> None:
    with pytest.raises(CoverageValidationError):
        derive_potential_support_assessments(
            value,
            support_profile(),
            coverages(),
        )


@pytest.mark.parametrize("value", [None, {}, "profile"])
def test_invalid_profile_type_is_rejected(value) -> None:
    with pytest.raises(CoverageProfileError):
        derive_potential_support_assessments(
            PROJECT_ID,
            value,
            coverages(),
        )


def test_inactive_profile_is_rejected() -> None:
    profile = support_profile()
    changed = replace(profile, status="retired")
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageProfileError):
        assess(coverages(), profile=changed)


def test_profile_fingerprint_mismatch_is_rejected() -> None:
    with pytest.raises(CoverageIntegrityError):
        assess(
            coverages(),
            profile=replace(support_profile(), profile_fingerprint="0" * 64),
        )


def test_empty_profile_is_rejected() -> None:
    profile = replace(support_profile(), support_targets=())
    profile = replace(
        profile,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            profile
        ),
    )
    with pytest.raises(CoverageProfileError):
        assess(coverages(), profile=profile)


def test_unsorted_profile_targets_are_rejected() -> None:
    profile = support_profile()
    changed = replace(profile, support_targets=tuple(reversed(profile.support_targets)))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageProfileError):
        assess(coverages(), profile=changed)


def test_non_contiguous_profile_order_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[1] = replace(targets[1], order=4)
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageProfileError):
        assess(coverages(), profile=changed)


def test_unknown_dependency_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[1] = replace(
        targets[1],
        required_support_target_ids=("SUPPORT_UNKNOWN",),
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageReferenceError):
        assess(coverages(), profile=changed)


def test_forward_dependency_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[0] = replace(
        targets[0],
        required_support_target_ids=("SUPPORT_SYSTEM_MODEL",),
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageReferenceError):
        assess(coverages(), profile=changed)


def test_duplicate_target_identity_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[1] = replace(
        targets[1],
        support_target_id=targets[0].support_target_id,
        required_support_target_ids=(),
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageIntegrityError):
        assess(coverages(), profile=changed)


def test_duplicate_required_node_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[0] = replace(
        targets[0],
        required_framework_node_ids=(STAKEHOLDER_NODES[0],) * 2,
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageIntegrityError):
        assess(coverages(), profile=changed)


def test_duplicate_dependency_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[1] = replace(
        targets[1],
        required_support_target_ids=(TARGET_IDS[0], TARGET_IDS[0]),
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageIntegrityError):
        assess(coverages(), profile=changed)


def test_self_dependency_is_rejected() -> None:
    profile = support_profile()
    targets = list(profile.support_targets)
    targets[0] = replace(
        targets[0],
        required_support_target_ids=(TARGET_IDS[0],),
    )
    changed = replace(profile, support_targets=tuple(targets))
    changed = replace(
        changed,
        profile_fingerprint=calculate_preliminary_support_profile_fingerprint(
            changed
        ),
    )
    with pytest.raises(CoverageIntegrityError):
        assess(coverages(), profile=changed)


def test_missing_required_node_coverage_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        assess(
            tuple(
                item
                for item in coverages()
                if item.framework_node_id != ALL_NODES[0]
            )
        )


def test_duplicate_node_coverage_is_rejected() -> None:
    selected = coverages()
    with pytest.raises(CoverageIntegrityError):
        assess(selected + (selected[0],))


def test_invalid_node_coverage_state_is_rejected() -> None:
    selected = list(coverages())
    selected[0] = replace(selected[0], coverage_state="invalid")
    with pytest.raises(CoverageValidationError):
        assess(tuple(selected))


def test_invalid_node_count_is_rejected() -> None:
    selected = list(coverages(covered_nodes=(ALL_NODES[0],)))
    selected[0] = replace(selected[0], eligible_source_count=2)
    with pytest.raises(CoverageIntegrityError):
        assess(tuple(selected))


def test_covering_counts_cannot_exceed_candidates() -> None:
    selected = list(coverages())
    selected[0] = replace(
        selected[0],
        confirmed_candidate_count=1,
        assignment_candidate_count=0,
    )
    with pytest.raises(CoverageIntegrityError):
        assess(tuple(selected))


def test_issue_from_another_project_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        assess(coverages(), issues=(issue(project_id="999999"),))


def test_issue_with_unknown_node_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        assess(coverages(), issues=(issue(node_id="FW_UNKNOWN"),))


def test_issue_with_unknown_target_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        assess(coverages(), issues=(issue(target_id="SUPPORT_UNKNOWN"),))


def test_duplicate_issue_identity_is_rejected() -> None:
    duplicate = issue("same")
    with pytest.raises(CoverageIntegrityError):
        assess(coverages(), issues=(duplicate, duplicate))


@pytest.mark.parametrize("level", ["error", "info", ""])
def test_invalid_issue_level_is_rejected(level: str) -> None:
    with pytest.raises(CoverageValidationError):
        assess(coverages(), issues=(issue(level=level),))


@pytest.mark.parametrize("value", [None, [], "coverages"])
def test_node_coverages_must_be_tuple(value) -> None:
    with pytest.raises(CoverageValidationError):
        derive_potential_support_assessments(
            PROJECT_ID,
            support_profile(),
            value,
        )


@pytest.mark.parametrize("value", [None, [], "issues"])
def test_issues_must_be_tuple(value) -> None:
    with pytest.raises(CoverageValidationError):
        derive_potential_support_assessments(
            PROJECT_ID,
            support_profile(),
            coverages(),
            value,
        )


def test_lookup_requires_tuple() -> None:
    with pytest.raises(CoverageValidationError):
        potential_support_by_id([], TARGET_IDS[0])


@pytest.mark.parametrize("value", [None, "", 1])
def test_lookup_requires_valid_id(value) -> None:
    with pytest.raises(CoverageValidationError):
        potential_support_by_id(assess(coverages()), value)