"""Derive deterministic framework-node, level and project coverage."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from modules.framework import mapping_target_ids, validate_framework_template

from .errors import (
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
)
from .types import (
    COVERAGE_EVIDENCE_STATES,
    COVERAGE_ISSUE_LEVELS,
    FRAMEWORK_LEVEL_COVERAGE_STATES,
    FRAMEWORK_NODE_COVERAGE_STATES,
    PROJECT_COVERAGE_STATES,
    CoverageIssue,
    FrameworkAssignmentCoverageEvidence,
    FrameworkLevelCoverage,
    FrameworkNodeCoverage,
)


PRELIMINARY_COVERAGE_ALGORITHM_ID = "TURING_PRELIMINARY_COVERAGE"
PRELIMINARY_COVERAGE_ALGORITHM_VERSION = "1.0.0"

_COVERING_EVIDENCE_STATES = frozenset(
    {"eligible_unreviewed", "eligible_confirmed"}
)
_PROJECT_BLOCKING_EVIDENCE_STATES = frozenset(
    {"excluded_invalid_reference"}
)


def derive_framework_node_coverages(
    project_id: str,
    framework_template: dict[str, Any],
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...],
    issues: tuple[CoverageIssue, ...] = (),
) -> tuple[FrameworkNodeCoverage, ...]:
    """Return one deterministic coverage record per mapping-target node."""

    _validate_project_id(project_id)
    template_nodes = _validated_template_nodes(framework_template)
    permitted_node_ids = set(template_nodes)
    evidence_by_node, all_evidence = _index_evidence(
        project_id,
        evidence,
        permitted_node_ids,
    )
    validated_issues = _validate_issues(project_id, issues)

    result: list[FrameworkNodeCoverage] = []
    for node_id, node in template_nodes.items():
        node_evidence = evidence_by_node.get(node_id, ())
        result.append(
            _derive_node_coverage(
                node,
                node_evidence,
                validated_issues,
            )
        )

    # Keep the variable explicit: validating all evidence is part of the
    # contract even when excluded evidence references no valid mapping node.
    assert len(all_evidence) == len(evidence)
    return tuple(result)


def derive_framework_level_coverages(
    framework_template: dict[str, Any],
    node_coverages: tuple[FrameworkNodeCoverage, ...],
) -> tuple[FrameworkLevelCoverage, ...]:
    """Aggregate exact node coverage into ordered framework levels."""

    level_nodes, mapping_nodes = _validated_framework_hierarchy(
        framework_template
    )
    coverage_by_id = _validate_node_coverage_collection(
        node_coverages,
        expected_node_ids=set(mapping_nodes),
    )

    result: list[FrameworkLevelCoverage] = []
    for level in level_nodes:
        children = tuple(
            node
            for node in mapping_nodes.values()
            if node["parent_node_id"] == level["node_id"]
        )
        ordered_children = tuple(
            sorted(children, key=lambda item: (item["order"], item["node_id"]))
        )
        child_coverages = tuple(
            coverage_by_id[node["node_id"]] for node in ordered_children
        )
        result.append(
            _derive_level_coverage(level, child_coverages)
        )
    return tuple(result)


def derive_project_coverage_state(
    node_coverages: tuple[FrameworkNodeCoverage, ...],
    *,
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...] = (),
    issues: tuple[CoverageIssue, ...] = (),
) -> str:
    """Return the canonical project coverage state with blocking precedence."""

    _require_tuple_of(
        node_coverages,
        FrameworkNodeCoverage,
        "node_coverages",
    )
    _require_tuple_of(
        evidence,
        FrameworkAssignmentCoverageEvidence,
        "evidence",
    )
    _require_tuple_of(issues, CoverageIssue, "issues")

    if not node_coverages:
        raise CoverageValidationError(
            "node_coverages must contain at least one mapping-target node."
        )
    node_ids = [item.framework_node_id for item in node_coverages]
    if len(node_ids) != len(set(node_ids)):
        raise CoverageIntegrityError(
            "Duplicate Framework Node Coverage identity."
        )
    _validate_node_coverage_instances(node_coverages)
    _validate_evidence_instances(evidence)
    _validate_issue_instances(issues)

    if any(issue.issue_level == "blocking" for issue in issues):
        return "attention_required"
    if any(
        item.evidence_state in _PROJECT_BLOCKING_EVIDENCE_STATES
        for item in evidence
    ):
        return "attention_required"

    covered = sum(
        item.coverage_state != "uncovered" for item in node_coverages
    )
    if covered == len(node_coverages):
        state = "covered"
    elif covered:
        state = "partially_covered"
    else:
        state = "uncovered"
    if state not in PROJECT_COVERAGE_STATES:
        raise CoverageIntegrityError(
            f"Unsupported derived project coverage state: {state}."
        )
    return state


def derive_project_preliminary_coverage(
    project_id: str,
    framework_template: dict[str, Any],
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...],
    issues: tuple[CoverageIssue, ...] = (),
) -> tuple[
    tuple[FrameworkNodeCoverage, ...],
    tuple[FrameworkLevelCoverage, ...],
    str,
]:
    """Derive node, level and project coverage from the same validated inputs."""

    node_coverages = derive_framework_node_coverages(
        project_id,
        framework_template,
        evidence,
        issues,
    )
    level_coverages = derive_framework_level_coverages(
        framework_template,
        node_coverages,
    )
    project_state = derive_project_coverage_state(
        node_coverages,
        evidence=evidence,
        issues=issues,
    )
    return node_coverages, level_coverages, project_state


def _derive_node_coverage(
    node: dict[str, Any],
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...],
    issues: tuple[CoverageIssue, ...],
) -> FrameworkNodeCoverage:
    covering = tuple(
        item
        for item in evidence
        if item.evidence_state in _COVERING_EVIDENCE_STATES
    )
    confirmed = tuple(
        item
        for item in covering
        if item.evidence_state == "eligible_confirmed"
    )
    unreviewed = tuple(
        item
        for item in covering
        if item.evidence_state == "eligible_unreviewed"
    )
    rejected = tuple(
        item
        for item in evidence
        if item.evidence_state == "excluded_rejected"
    )
    ambiguous = tuple(
        item
        for item in evidence
        if item.evidence_state == "excluded_ambiguous"
    )
    conflicting = tuple(
        item
        for item in evidence
        if item.evidence_state == "excluded_conflict"
    )

    if confirmed:
        coverage_state = "reviewed_candidate_covered"
    elif unreviewed:
        coverage_state = "candidate_covered"
    else:
        coverage_state = "uncovered"
    if coverage_state not in FRAMEWORK_NODE_COVERAGE_STATES:
        raise CoverageIntegrityError(
            f"Unsupported node coverage state: {coverage_state}."
        )

    all_candidate_ids = {
        item.framework_assignment_candidate_id for item in evidence
    }
    all_source_ids = {item.source_id for item in covering}
    all_information_unit_ids = {
        item.information_unit_id for item in covering
    }
    decision_ids = {
        item.human_review_decision_id
        for item in evidence
        if item.human_review_decision_id is not None
    }
    direct_issues = tuple(
        issue
        for issue in issues
        if _issue_applies_to_node(
            issue,
            node["node_id"],
            evidence,
        )
    )
    issue_codes = {
        code for item in evidence for code in item.issue_codes
    }
    issue_codes.update(issue.code for issue in direct_issues)
    attention_required = any(
        item.attention_required for item in evidence
    ) or bool(direct_issues)

    return FrameworkNodeCoverage(
        framework_node_id=node["node_id"],
        mapping_key=node["mapping_key"],
        node_name=node["name"],
        level_node_id=node["parent_node_id"],
        coverage_state=coverage_state,
        attention_required=attention_required,
        eligible_source_count=len(all_source_ids),
        information_unit_count=len(all_information_unit_ids),
        assignment_candidate_count=len(covering),
        confirmed_candidate_count=len(confirmed),
        unreviewed_candidate_count=len(unreviewed),
        rejected_candidate_count=len(rejected),
        ambiguous_candidate_count=len(ambiguous),
        conflicting_candidate_count=len(conflicting),
        source_ids=tuple(sorted(all_source_ids)),
        information_unit_ids=tuple(sorted(all_information_unit_ids)),
        framework_assignment_candidate_ids=tuple(
            sorted(all_candidate_ids)
        ),
        human_review_decision_ids=tuple(sorted(decision_ids)),
        issue_codes=tuple(sorted(issue_codes)),
    )


def _derive_level_coverage(
    level: dict[str, Any],
    node_coverages: tuple[FrameworkNodeCoverage, ...],
) -> FrameworkLevelCoverage:
    if not node_coverages:
        raise CoverageIntegrityError(
            f"Framework level has no mapping-target nodes: {level['node_id']}."
        )
    covered = tuple(
        item for item in node_coverages if item.coverage_state != "uncovered"
    )
    candidate = tuple(
        item
        for item in node_coverages
        if item.coverage_state == "candidate_covered"
    )
    reviewed = tuple(
        item
        for item in node_coverages
        if item.coverage_state == "reviewed_candidate_covered"
    )
    attention = tuple(
        item for item in node_coverages if item.attention_required
    )

    if not covered:
        state = "uncovered"
    elif len(covered) == len(node_coverages):
        state = "covered"
    else:
        state = "partially_covered"
    if state not in FRAMEWORK_LEVEL_COVERAGE_STATES:
        raise CoverageIntegrityError(
            f"Unsupported level coverage state: {state}."
        )

    return FrameworkLevelCoverage(
        level_node_id=level["node_id"],
        level_name=level["name"],
        coverage_state=state,
        covered_node_count=len(covered),
        total_node_count=len(node_coverages),
        candidate_covered_node_count=len(candidate),
        reviewed_candidate_covered_node_count=len(reviewed),
        attention_node_count=len(attention),
        covered_node_ids=tuple(
            item.framework_node_id for item in covered
        ),
        uncovered_node_ids=tuple(
            item.framework_node_id
            for item in node_coverages
            if item.coverage_state == "uncovered"
        ),
        attention_node_ids=tuple(
            item.framework_node_id for item in attention
        ),
    )


def _validated_template_nodes(
    framework_template: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    _, mapping_nodes = _validated_framework_hierarchy(framework_template)
    return mapping_nodes


def _validated_framework_hierarchy(
    framework_template: dict[str, Any],
) -> tuple[tuple[dict[str, Any], ...], dict[str, dict[str, Any]]]:
    if not isinstance(framework_template, dict):
        raise CoverageValidationError(
            "framework_template must be a dictionary."
        )
    try:
        validate_framework_template(framework_template)
        permitted = mapping_target_ids(framework_template)
    except Exception as exc:
        raise CoverageValidationError(
            "framework_template violates the framework contract."
        ) from exc

    levels = tuple(
        sorted(
            (
                node
                for node in framework_template["nodes"]
                if node["node_type"] == "level"
            ),
            key=lambda item: (item["order"], item["node_id"]),
        )
    )
    level_ids = {item["node_id"] for item in levels}
    mapping_nodes_list = tuple(
        sorted(
            (
                node
                for node in framework_template["nodes"]
                if node["node_id"] in permitted
            ),
            key=lambda item: (
                _level_order(item["parent_node_id"], levels),
                item["order"],
                item["node_id"],
            ),
        )
    )
    for node in mapping_nodes_list:
        if node["parent_node_id"] not in level_ids:
            raise CoverageIntegrityError(
                "Mapping-target node does not reference a framework level: "
                f"{node['node_id']}."
            )
    return levels, {item["node_id"]: item for item in mapping_nodes_list}


def _level_order(
    level_id: str,
    levels: tuple[dict[str, Any], ...],
) -> int:
    for level in levels:
        if level["node_id"] == level_id:
            return level["order"]
    raise CoverageIntegrityError(
        f"Unknown framework level reference: {level_id}."
    )


def _index_evidence(
    project_id: str,
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...],
    permitted_node_ids: set[str],
) -> tuple[
    dict[str, tuple[FrameworkAssignmentCoverageEvidence, ...]],
    tuple[FrameworkAssignmentCoverageEvidence, ...],
]:
    _require_tuple_of(
        evidence,
        FrameworkAssignmentCoverageEvidence,
        "evidence",
    )
    candidate_ids: set[str] = set()
    by_node: dict[str, list[FrameworkAssignmentCoverageEvidence]] = {}
    ordered = tuple(
        sorted(
            evidence,
            key=lambda item: item.framework_assignment_candidate_id,
        )
    )
    for item in ordered:
        if item.project_id != project_id:
            raise CoverageReferenceError(
                "Coverage evidence belongs to another project: "
                f"{item.framework_assignment_candidate_id}."
            )
        if item.evidence_state not in COVERAGE_EVIDENCE_STATES:
            raise CoverageIntegrityError(
                "Unsupported coverage evidence state: "
                f"{item.evidence_state}."
            )
        if item.framework_assignment_candidate_id in candidate_ids:
            raise CoverageIntegrityError(
                "Duplicate Framework Assignment Coverage Evidence identity: "
                f"{item.framework_assignment_candidate_id}."
            )
        candidate_ids.add(item.framework_assignment_candidate_id)
        if len(item.framework_node_ids) != len(set(item.framework_node_ids)):
            raise CoverageIntegrityError(
                "Coverage evidence contains duplicate framework node IDs: "
                f"{item.framework_assignment_candidate_id}."
            )
        unknown_nodes = set(item.framework_node_ids) - permitted_node_ids
        if (
            unknown_nodes
            and item.evidence_state in _COVERING_EVIDENCE_STATES
        ):
            raise CoverageReferenceError(
                "Eligible coverage evidence references unknown framework nodes: "
                + ", ".join(sorted(unknown_nodes))
                + "."
            )
        for node_id in sorted(set(item.framework_node_ids) & permitted_node_ids):
            by_node.setdefault(node_id, []).append(item)
    return (
        {
            node_id: tuple(items)
            for node_id, items in by_node.items()
        },
        ordered,
    )


def _validate_issues(
    project_id: str,
    issues: tuple[CoverageIssue, ...],
) -> tuple[CoverageIssue, ...]:
    _require_tuple_of(issues, CoverageIssue, "issues")
    seen: set[tuple[Any, ...]] = set()
    ordered = tuple(
        sorted(
            issues,
            key=lambda item: (
                item.issue_level,
                item.code,
                item.message,
                "" if item.framework_node_id is None else item.framework_node_id,
                ""
                if item.framework_assignment_candidate_id is None
                else item.framework_assignment_candidate_id,
            ),
        )
    )
    for issue in ordered:
        if issue.project_id != project_id:
            raise CoverageReferenceError(
                f"Coverage issue belongs to another project: {issue.code}."
            )
        if issue.issue_level not in COVERAGE_ISSUE_LEVELS:
            raise CoverageIntegrityError(
                f"Unsupported coverage issue level: {issue.issue_level}."
            )
        identity = (
            issue.code,
            issue.message,
            issue.issue_level,
            issue.path,
            issue.source_id,
            issue.information_unit_id,
            issue.framework_node_id,
            issue.framework_assignment_candidate_id,
            issue.human_review_decision_id,
            issue.support_target_id,
        )
        if identity in seen:
            raise CoverageIntegrityError(
                f"Duplicate Coverage Issue: {issue.code}."
            )
        seen.add(identity)
    return ordered


def _issue_applies_to_node(
    issue: CoverageIssue,
    node_id: str,
    evidence: tuple[FrameworkAssignmentCoverageEvidence, ...],
) -> bool:
    if issue.framework_node_id is not None:
        return issue.framework_node_id == node_id
    candidate_ids = {
        item.framework_assignment_candidate_id for item in evidence
    }
    if issue.framework_assignment_candidate_id is not None:
        return issue.framework_assignment_candidate_id in candidate_ids
    source_ids = {item.source_id for item in evidence}
    if issue.source_id is not None:
        return issue.source_id in source_ids
    information_unit_ids = {
        item.information_unit_id for item in evidence
    }
    if issue.information_unit_id is not None:
        return issue.information_unit_id in information_unit_ids
    return False


def _validate_node_coverage_collection(
    node_coverages: tuple[FrameworkNodeCoverage, ...],
    *,
    expected_node_ids: set[str],
) -> dict[str, FrameworkNodeCoverage]:
    _require_tuple_of(
        node_coverages,
        FrameworkNodeCoverage,
        "node_coverages",
    )
    _validate_node_coverage_instances(node_coverages)
    by_id: dict[str, FrameworkNodeCoverage] = {}
    for item in node_coverages:
        if item.framework_node_id in by_id:
            raise CoverageIntegrityError(
                "Duplicate Framework Node Coverage identity: "
                f"{item.framework_node_id}."
            )
        by_id[item.framework_node_id] = item
    missing = expected_node_ids - set(by_id)
    extra = set(by_id) - expected_node_ids
    if missing:
        raise CoverageReferenceError(
            "Missing Framework Node Coverage records: "
            + ", ".join(sorted(missing))
            + "."
        )
    if extra:
        raise CoverageReferenceError(
            "Unknown Framework Node Coverage records: "
            + ", ".join(sorted(extra))
            + "."
        )
    return by_id


def _validate_node_coverage_instances(
    node_coverages: Iterable[FrameworkNodeCoverage],
) -> None:
    for item in node_coverages:
        if item.coverage_state not in FRAMEWORK_NODE_COVERAGE_STATES:
            raise CoverageIntegrityError(
                f"Unsupported node coverage state: {item.coverage_state}."
            )
        if any(
            count < 0
            for count in (
                item.eligible_source_count,
                item.information_unit_count,
                item.assignment_candidate_count,
                item.confirmed_candidate_count,
                item.unreviewed_candidate_count,
                item.rejected_candidate_count,
                item.ambiguous_candidate_count,
                item.conflicting_candidate_count,
            )
        ):
            raise CoverageIntegrityError(
                "Framework Node Coverage counts must not be negative: "
                f"{item.framework_node_id}."
            )
        if item.eligible_source_count != len(item.source_ids):
            raise CoverageIntegrityError(
                "eligible_source_count disagrees with source_ids: "
                f"{item.framework_node_id}."
            )
        if item.information_unit_count != len(item.information_unit_ids):
            raise CoverageIntegrityError(
                "information_unit_count disagrees with information_unit_ids: "
                f"{item.framework_node_id}."
            )
        if (
            item.assignment_candidate_count
            != item.confirmed_candidate_count
            + item.unreviewed_candidate_count
        ):
            raise CoverageIntegrityError(
                "Covering candidate counts are inconsistent: "
                f"{item.framework_node_id}."
            )
        for values, label in (
            (item.source_ids, "source_ids"),
            (item.information_unit_ids, "information_unit_ids"),
            (
                item.framework_assignment_candidate_ids,
                "framework_assignment_candidate_ids",
            ),
            (item.human_review_decision_ids, "human_review_decision_ids"),
            (item.issue_codes, "issue_codes"),
        ):
            if tuple(sorted(set(values))) != values:
                raise CoverageIntegrityError(
                    f"{label} must be unique and sorted for "
                    f"{item.framework_node_id}."
                )


def _validate_evidence_instances(
    evidence: Iterable[FrameworkAssignmentCoverageEvidence],
) -> None:
    candidate_ids: set[str] = set()
    for item in evidence:
        if item.evidence_state not in COVERAGE_EVIDENCE_STATES:
            raise CoverageIntegrityError(
                f"Unsupported coverage evidence state: {item.evidence_state}."
            )
        if item.framework_assignment_candidate_id in candidate_ids:
            raise CoverageIntegrityError(
                "Duplicate Framework Assignment Coverage Evidence identity."
            )
        candidate_ids.add(item.framework_assignment_candidate_id)


def _validate_issue_instances(issues: Iterable[CoverageIssue]) -> None:
    for issue in issues:
        if issue.issue_level not in COVERAGE_ISSUE_LEVELS:
            raise CoverageIntegrityError(
                f"Unsupported coverage issue level: {issue.issue_level}."
            )


def _validate_project_id(project_id: str) -> None:
    if not isinstance(project_id, str) or not project_id:
        raise CoverageValidationError(
            "project_id must be a non-empty string."
        )


def _require_tuple_of(value: object, data_type: type, label: str) -> None:
    if not isinstance(value, tuple) or not all(
        isinstance(item, data_type) for item in value
    ):
        raise CoverageValidationError(
            f"{label} must be a tuple of {data_type.__name__} values."
        )