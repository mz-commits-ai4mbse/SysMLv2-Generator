from dataclasses import replace
from pathlib import Path

import pytest

from modules.framework import load_framework_template
from modules.project_coverage.coverage import (
    PRELIMINARY_COVERAGE_ALGORITHM_ID,
    PRELIMINARY_COVERAGE_ALGORITHM_VERSION,
    derive_framework_level_coverages,
    derive_framework_node_coverages,
    derive_project_coverage_state,
    derive_project_preliminary_coverage,
)
from modules.project_coverage.errors import (
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
)
from modules.project_coverage.types import (
    CoverageIssue,
    FrameworkAssignmentCoverageEvidence,
    FrameworkNodeCoverage,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_PATH = ROOT / "context/frameworks/turing_rflp_framework.json"
PROJECT_ID = "318604"

STAKEHOLDERS = "FW_STAKEHOLDER_STAKEHOLDERS"
USER_NEEDS = "FW_STAKEHOLDER_USER_NEEDS"
STAKEHOLDER_REQUIREMENTS = "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS"
USE_CASES = "FW_STAKEHOLDER_USE_CASES"
SYSTEM_REQUIREMENTS = "FW_SYSTEM_REQUIREMENTS"
SYSTEM_FUNCTIONAL = "FW_SYSTEM_FUNCTIONAL"
SYSTEM_LOGICAL = "FW_SYSTEM_LOGICAL"
SYSTEM_PHYSICAL = "FW_SYSTEM_PHYSICAL"
SUBSYSTEM_REQUIREMENTS = "FW_SUBSYSTEM_REQUIREMENTS"
SUBSYSTEM_FUNCTIONAL = "FW_SUBSYSTEM_FUNCTIONAL"
SUBSYSTEM_LOGICAL = "FW_SUBSYSTEM_LOGICAL"
SUBSYSTEM_PHYSICAL = "FW_SUBSYSTEM_PHYSICAL"


def framework():
    return load_framework_template(FRAMEWORK_PATH)


def evidence(
    sequence: int = 1,
    *,
    state: str = "eligible_unreviewed",
    nodes: tuple[str, ...] = (STAKEHOLDERS,),
    source_id: str | None = None,
    information_unit_id: str | None = None,
    decision_id: str | None = None,
    attention: bool = False,
    issue_codes: tuple[str, ...] = (),
    project_id: str = PROJECT_ID,
):
    return FrameworkAssignmentCoverageEvidence(
        project_id=project_id,
        source_id=source_id or f"SRC-{sequence:06d}",
        information_unit_id=information_unit_id or f"IU-{sequence:06d}",
        framework_assignment_candidate_id=f"FAC-{sequence:06d}",
        evidence_state=state,
        framework_node_ids=nodes,
        human_review_decision_id=decision_id,
        attention_required=attention,
        issue_codes=issue_codes,
    )


def issue(
    code: str = "coverage_warning",
    *,
    level: str = "warning",
    node_id: str | None = None,
    candidate_id: str | None = None,
    source_id: str | None = None,
    information_unit_id: str | None = None,
    project_id: str = PROJECT_ID,
):
    return CoverageIssue(
        project_id=project_id,
        code=code,
        message=f"Issue {code}",
        issue_level=level,
        framework_node_id=node_id,
        framework_assignment_candidate_id=candidate_id,
        source_id=source_id,
        information_unit_id=information_unit_id,
    )


def node_by_id(items, node_id):
    return next(item for item in items if item.framework_node_id == node_id)


def level_by_id(items, level_id):
    return next(item for item in items if item.level_node_id == level_id)


def all_node_ids():
    return (
        STAKEHOLDERS,
        USER_NEEDS,
        STAKEHOLDER_REQUIREMENTS,
        USE_CASES,
        SYSTEM_REQUIREMENTS,
        SYSTEM_FUNCTIONAL,
        SYSTEM_LOGICAL,
        SYSTEM_PHYSICAL,
        SUBSYSTEM_REQUIREMENTS,
        SUBSYSTEM_FUNCTIONAL,
        SUBSYSTEM_LOGICAL,
        SUBSYSTEM_PHYSICAL,
    )


def test_algorithm_contract() -> None:
    assert PRELIMINARY_COVERAGE_ALGORITHM_ID == "TURING_PRELIMINARY_COVERAGE"
    assert PRELIMINARY_COVERAGE_ALGORITHM_VERSION == "1.0.0"


def test_empty_evidence_creates_twelve_uncovered_nodes() -> None:
    items = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    assert len(items) == 12
    assert [item.framework_node_id for item in items] == list(all_node_ids())
    assert {item.coverage_state for item in items} == {"uncovered"}


def test_unreviewed_evidence_creates_candidate_coverage() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID, framework(), (evidence(),)
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "candidate_covered"
    assert item.assignment_candidate_count == 1
    assert item.unreviewed_candidate_count == 1
    assert item.confirmed_candidate_count == 0


def test_confirmed_evidence_creates_reviewed_coverage() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(
                state="eligible_confirmed",
                decision_id="HRD-000001",
            ),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "reviewed_candidate_covered"
    assert item.confirmed_candidate_count == 1
    assert item.human_review_decision_ids == ("HRD-000001",)


def test_confirmed_coverage_has_display_precedence() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1),
            evidence(
                2,
                state="eligible_confirmed",
                decision_id="HRD-000002",
            ),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "reviewed_candidate_covered"
    assert item.assignment_candidate_count == 2
    assert item.confirmed_candidate_count == 1
    assert item.unreviewed_candidate_count == 1


def test_same_source_is_counted_once() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1, source_id="SRC-000001"),
            evidence(2, source_id="SRC-000001"),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.eligible_source_count == 1
    assert item.source_ids == ("SRC-000001",)
    assert item.information_unit_count == 2


def test_same_information_unit_is_counted_once() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1, information_unit_id="IU-000001"),
            evidence(2, information_unit_id="IU-000001"),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.information_unit_count == 1
    assert item.information_unit_ids == ("IU-000001",)


def test_one_candidate_may_cover_multiple_nodes() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (evidence(nodes=(STAKEHOLDERS, USER_NEEDS)),),
    )
    assert node_by_id(items, STAKEHOLDERS).coverage_state == "candidate_covered"
    assert node_by_id(items, USER_NEEDS).coverage_state == "candidate_covered"


@pytest.mark.parametrize(
    ("state", "field", "attention"),
    [
        ("excluded_rejected", "rejected_candidate_count", False),
        ("excluded_ambiguous", "ambiguous_candidate_count", True),
        ("excluded_conflict", "conflicting_candidate_count", True),
    ],
)
def test_non_covering_states_are_counted_without_coverage(
    state, field, attention
) -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(
                state=state,
                attention=attention,
                decision_id=(
                    "HRD-000001" if state == "excluded_rejected" else None
                ),
            ),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "uncovered"
    assert getattr(item, field) == 1
    assert item.attention_required is attention
    assert item.assignment_candidate_count == 0


def test_request_changes_remains_auditable_and_attention_required() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(
                state="excluded_request_changes",
                decision_id="HRD-000001",
                attention=True,
                issue_codes=("framework_assignment_changes_requested",),
            ),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "uncovered"
    assert item.attention_required is True
    assert item.framework_assignment_candidate_ids == ("FAC-000001",)
    assert item.human_review_decision_ids == ("HRD-000001",)
    assert item.issue_codes == ("framework_assignment_changes_requested",)


def test_excluded_source_does_not_create_coverage_or_attention() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (evidence(state="excluded_source"),),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "uncovered"
    assert item.attention_required is False
    assert item.eligible_source_count == 0


@pytest.mark.parametrize(
    "state", ["excluded_invalidated", "excluded_invalid_reference"]
)
def test_invalid_evidence_marks_node_attention(state) -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (evidence(state=state, attention=True, issue_codes=(state,)),),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.attention_required is True
    assert state in item.issue_codes


def test_node_can_be_covered_and_require_attention() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1),
            evidence(
                2,
                state="excluded_conflict",
                attention=True,
                issue_codes=("framework_assignment_conflict",),
            ),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.coverage_state == "candidate_covered"
    assert item.attention_required is True
    assert item.conflicting_candidate_count == 1


def test_direct_node_issue_is_attached() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (),
        (issue(node_id=STAKEHOLDERS),),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.attention_required is True
    assert item.issue_codes == ("coverage_warning",)


@pytest.mark.parametrize(
    ("selector", "value"),
    [
        ("candidate_id", "FAC-000001"),
        ("source_id", "SRC-000001"),
        ("information_unit_id", "IU-000001"),
    ],
)
def test_referenced_issue_is_attached(selector, value) -> None:
    kwargs = {selector: value}
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (evidence(),),
        (issue(**kwargs),),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.attention_required is True
    assert item.issue_codes == ("coverage_warning",)


def test_project_wide_issue_is_not_duplicated_to_every_node() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (),
        (issue(),),
    )
    assert not any(item.attention_required for item in items)


def test_identifiers_and_issue_codes_are_unique_and_sorted() -> None:
    items = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(2, issue_codes=("z", "a")),
            evidence(1, issue_codes=("a",)),
        ),
    )
    item = node_by_id(items, STAKEHOLDERS)
    assert item.framework_assignment_candidate_ids == (
        "FAC-000001", "FAC-000002"
    )
    assert item.issue_codes == ("a", "z")


def test_level_coverage_order_and_counts() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1, nodes=(STAKEHOLDERS,)),
            evidence(2, nodes=(USER_NEEDS,)),
        ),
    )
    levels = derive_framework_level_coverages(framework(), nodes)
    assert [item.level_node_id for item in levels] == [
        "FW_LEVEL_STAKEHOLDER",
        "FW_LEVEL_SYSTEM",
        "FW_LEVEL_SUBSYSTEM",
    ]
    stakeholder = level_by_id(levels, "FW_LEVEL_STAKEHOLDER")
    assert stakeholder.coverage_state == "partially_covered"
    assert stakeholder.covered_node_count == 2
    assert stakeholder.total_node_count == 4
    assert stakeholder.candidate_covered_node_count == 2
    assert stakeholder.reviewed_candidate_covered_node_count == 0


def test_fully_covered_level() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        tuple(
            evidence(index, nodes=(node_id,))
            for index, node_id in enumerate(all_node_ids()[:4], start=1)
        ),
    )
    stakeholder = level_by_id(
        derive_framework_level_coverages(framework(), nodes),
        "FW_LEVEL_STAKEHOLDER",
    )
    assert stakeholder.coverage_state == "covered"
    assert stakeholder.covered_node_ids == all_node_ids()[:4]
    assert stakeholder.uncovered_node_ids == ()


def test_uncovered_level() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    system = level_by_id(
        derive_framework_level_coverages(framework(), nodes),
        "FW_LEVEL_SYSTEM",
    )
    assert system.coverage_state == "uncovered"
    assert system.covered_node_count == 0
    assert system.uncovered_node_ids == all_node_ids()[4:8]


def test_level_attention_counts_are_separate() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (
            evidence(1, nodes=(STAKEHOLDERS,)),
            evidence(
                2,
                state="excluded_conflict",
                nodes=(STAKEHOLDERS,),
                attention=True,
            ),
        ),
    )
    stakeholder = level_by_id(
        derive_framework_level_coverages(framework(), nodes),
        "FW_LEVEL_STAKEHOLDER",
    )
    assert stakeholder.coverage_state == "partially_covered"
    assert stakeholder.attention_node_count == 1
    assert stakeholder.attention_node_ids == (STAKEHOLDERS,)


def test_project_state_uncovered() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    assert derive_project_coverage_state(nodes) == "uncovered"


def test_project_state_partially_covered() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID, framework(), (evidence(),)
    )
    assert derive_project_coverage_state(nodes) == "partially_covered"


def test_project_state_covered() -> None:
    items = tuple(
        evidence(index, nodes=(node_id,))
        for index, node_id in enumerate(all_node_ids(), start=1)
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert derive_project_coverage_state(nodes) == "covered"


def test_nonblocking_node_attention_does_not_override_project_state() -> None:
    items = (
        evidence(1),
        evidence(
            2,
            state="excluded_conflict",
            attention=True,
        ),
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert derive_project_coverage_state(nodes, evidence=items) == "partially_covered"


def test_blocking_issue_overrides_project_state() -> None:
    items = tuple(
        evidence(index, nodes=(node_id,))
        for index, node_id in enumerate(all_node_ids(), start=1)
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert derive_project_coverage_state(
        nodes,
        evidence=items,
        issues=(issue(level="blocking"),),
    ) == "attention_required"


def test_invalid_reference_evidence_overrides_project_state() -> None:
    items = (
        evidence(
            state="excluded_invalid_reference",
            attention=True,
        ),
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert derive_project_coverage_state(nodes, evidence=items) == "attention_required"


def test_invalidated_historic_evidence_does_not_automatically_override() -> None:
    items = (
        evidence(
            state="excluded_invalidated",
            attention=True,
        ),
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert derive_project_coverage_state(nodes, evidence=items) == "uncovered"


def test_wrapper_returns_consistent_results() -> None:
    nodes, levels, state = derive_project_preliminary_coverage(
        PROJECT_ID, framework(), (evidence(),)
    )
    assert len(nodes) == 12
    assert len(levels) == 3
    assert state == "partially_covered"


def test_evidence_input_order_does_not_change_result() -> None:
    first = (evidence(2), evidence(1, nodes=(USER_NEEDS,)))
    second = tuple(reversed(first))
    assert derive_project_preliminary_coverage(
        PROJECT_ID, framework(), first
    ) == derive_project_preliminary_coverage(
        PROJECT_ID, framework(), second
    )


def test_empty_project_id_rejected() -> None:
    with pytest.raises(CoverageValidationError, match="project_id"):
        derive_framework_node_coverages("", framework(), ())


def test_framework_template_must_be_dictionary() -> None:
    with pytest.raises(CoverageValidationError, match="dictionary"):
        derive_framework_node_coverages(PROJECT_ID, [], ())


def test_invalid_framework_template_rejected() -> None:
    broken = framework()
    broken["nodes"] = []
    with pytest.raises(CoverageValidationError, match="framework contract"):
        derive_framework_node_coverages(PROJECT_ID, broken, ())


def test_evidence_collection_must_be_tuple() -> None:
    with pytest.raises(CoverageValidationError, match="tuple"):
        derive_framework_node_coverages(PROJECT_ID, framework(), [])


def test_evidence_collection_requires_exact_type() -> None:
    with pytest.raises(CoverageValidationError, match="tuple"):
        derive_framework_node_coverages(PROJECT_ID, framework(), (object(),))


def test_mixed_project_evidence_rejected() -> None:
    with pytest.raises(CoverageReferenceError, match="another project"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (evidence(project_id="999999"),),
        )


def test_duplicate_candidate_evidence_rejected() -> None:
    with pytest.raises(CoverageIntegrityError, match="Duplicate"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (evidence(), evidence()),
        )


def test_duplicate_node_reference_in_evidence_rejected() -> None:
    with pytest.raises(CoverageIntegrityError, match="duplicate framework"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (evidence(nodes=(STAKEHOLDERS, STAKEHOLDERS)),),
        )


def test_unknown_node_in_eligible_evidence_rejected() -> None:
    with pytest.raises(CoverageReferenceError, match="unknown framework"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (evidence(nodes=("FW_UNKNOWN",)),),
        )


def test_unknown_node_in_invalid_reference_evidence_is_project_attention() -> None:
    items = (
        evidence(
            state="excluded_invalid_reference",
            nodes=("FW_UNKNOWN",),
            attention=True,
        ),
    )
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), items)
    assert len(nodes) == 12
    assert derive_project_coverage_state(nodes, evidence=items) == "attention_required"


def test_unsupported_evidence_state_rejected() -> None:
    with pytest.raises(CoverageIntegrityError, match="Unsupported"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (evidence(state="unknown"),),
        )


def test_issue_collection_must_be_tuple() -> None:
    with pytest.raises(CoverageValidationError, match="tuple"):
        derive_framework_node_coverages(PROJECT_ID, framework(), (), [])


def test_mixed_project_issue_rejected() -> None:
    with pytest.raises(CoverageReferenceError, match="another project"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (),
            (issue(project_id="999999"),),
        )


def test_unsupported_issue_level_rejected() -> None:
    with pytest.raises(CoverageIntegrityError, match="issue level"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (),
            (issue(level="fatal"),),
        )


def test_duplicate_issue_rejected() -> None:
    duplicate = issue(node_id=STAKEHOLDERS)
    with pytest.raises(CoverageIntegrityError, match="Duplicate"):
        derive_framework_node_coverages(
            PROJECT_ID,
            framework(),
            (),
            (duplicate, duplicate),
        )


def test_level_aggregation_requires_all_nodes() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    with pytest.raises(CoverageReferenceError, match="Missing"):
        derive_framework_level_coverages(framework(), nodes[:-1])


def test_level_aggregation_rejects_unknown_node() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    unknown = replace(nodes[0], framework_node_id="FW_UNKNOWN")
    with pytest.raises(CoverageReferenceError, match="Missing|Unknown"):
        derive_framework_level_coverages(framework(), (unknown,) + nodes[1:])


def test_level_aggregation_rejects_duplicate_node() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    with pytest.raises(CoverageIntegrityError, match="Duplicate"):
        derive_framework_level_coverages(framework(), nodes + (nodes[0],))


def test_node_count_mismatch_is_rejected() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID, framework(), (evidence(),)
    )
    broken = replace(nodes[0], eligible_source_count=99)
    with pytest.raises(CoverageIntegrityError, match="eligible_source_count"):
        derive_framework_level_coverages(framework(), (broken,) + nodes[1:])


def test_covering_candidate_count_mismatch_is_rejected() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID, framework(), (evidence(),)
    )
    broken = replace(nodes[0], assignment_candidate_count=2)
    with pytest.raises(CoverageIntegrityError, match="inconsistent"):
        derive_framework_level_coverages(framework(), (broken,) + nodes[1:])


def test_unsorted_identifier_tuple_is_rejected() -> None:
    nodes = derive_framework_node_coverages(
        PROJECT_ID,
        framework(),
        (evidence(1), evidence(2)),
    )
    broken = replace(
        nodes[0],
        framework_assignment_candidate_ids=("FAC-000002", "FAC-000001"),
    )
    with pytest.raises(CoverageIntegrityError, match="unique and sorted"):
        derive_framework_level_coverages(framework(), (broken,) + nodes[1:])


def test_project_state_requires_nonempty_nodes() -> None:
    with pytest.raises(CoverageValidationError, match="at least one"):
        derive_project_coverage_state(())


def test_project_state_collection_must_be_tuple() -> None:
    with pytest.raises(CoverageValidationError, match="tuple"):
        derive_project_coverage_state([])


def test_project_state_rejects_invalid_node_state() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    broken = replace(nodes[0], coverage_state="unknown")
    with pytest.raises(CoverageIntegrityError, match="Unsupported"):
        derive_project_coverage_state((broken,) + nodes[1:])


def test_project_state_rejects_invalid_issue_level() -> None:
    nodes = derive_framework_node_coverages(PROJECT_ID, framework(), ())
    with pytest.raises(CoverageIntegrityError, match="issue level"):
        derive_project_coverage_state(
            nodes,
            issues=(issue(level="fatal"),),
        )