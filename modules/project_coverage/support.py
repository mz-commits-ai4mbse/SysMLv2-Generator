"""Derive deterministic preliminary model and SubModel support."""

from __future__ import annotations

from .errors import (
    CoverageIntegrityError,
    CoverageProfileError,
    CoverageReferenceError,
    CoverageValidationError,
)
from .profile import calculate_preliminary_support_profile_fingerprint
from .types import (
    COVERAGE_ISSUE_LEVELS,
    FRAMEWORK_NODE_COVERAGE_STATES,
    POTENTIAL_SUPPORT_STATES,
    SUPPORT_PROFILE_STATUSES,
    SUPPORT_TARGET_TYPES,
    CoverageIssue,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    PreliminarySupportProfile,
    PreliminarySupportTarget,
)


PRELIMINARY_SUPPORT_ALGORITHM_ID = "TURING_PRELIMINARY_MODEL_SUPPORT"
PRELIMINARY_SUPPORT_ALGORITHM_VERSION = "1.0.0"


def derive_potential_support_assessments(
    project_id: str,
    support_profile: PreliminarySupportProfile,
    node_coverages: tuple[FrameworkNodeCoverage, ...],
    issues: tuple[CoverageIssue, ...] = (),
) -> tuple[PotentialSupportAssessment, ...]:
    """Derive one ordered support assessment per versioned profile target."""

    _validate_project_id(project_id)
    targets = _validate_support_profile(support_profile)
    coverage_by_id = _validate_node_coverages(node_coverages)
    validated_issues = _validate_issues(
        project_id,
        issues,
        known_node_ids=set(coverage_by_id),
        known_support_target_ids={
            target.support_target_id for target in targets
        },
    )

    required_node_ids = {
        node_id
        for target in targets
        for node_id in target.required_framework_node_ids
    }
    missing_coverage_records = required_node_ids - coverage_by_id.keys()
    if missing_coverage_records:
        raise CoverageReferenceError(
            "Missing Framework Node Coverage records required by the "
            "Preliminary Support Profile: "
            + ", ".join(sorted(missing_coverage_records))
            + "."
        )

    result: list[PotentialSupportAssessment] = []
    assessments_by_id: dict[str, PotentialSupportAssessment] = {}
    for target in targets:
        assessment = _derive_target_assessment(
            target,
            coverage_by_id,
            assessments_by_id,
            validated_issues,
        )
        result.append(assessment)
        assessments_by_id[target.support_target_id] = assessment
    return tuple(result)


def potential_support_by_id(
    assessments: tuple[PotentialSupportAssessment, ...],
    support_target_id: str,
) -> PotentialSupportAssessment:
    """Return one exact support assessment by stable target identifier."""

    _require_tuple_of(
        assessments,
        PotentialSupportAssessment,
        "assessments",
    )
    if not isinstance(support_target_id, str) or not support_target_id:
        raise CoverageValidationError(
            "support_target_id must be a non-empty string."
        )
    matches = tuple(
        item
        for item in assessments
        if item.support_target_id == support_target_id
    )
    if not matches:
        raise CoverageReferenceError(
            f"Unknown support_target_id: {support_target_id!r}."
        )
    if len(matches) > 1:
        raise CoverageIntegrityError(
            f"Duplicate Potential Support Assessment: {support_target_id}."
        )
    return matches[0]


def _derive_target_assessment(
    target: PreliminarySupportTarget,
    coverage_by_id: dict[str, FrameworkNodeCoverage],
    assessments_by_id: dict[str, PotentialSupportAssessment],
    issues: tuple[CoverageIssue, ...],
) -> PotentialSupportAssessment:
    required_coverages = tuple(
        coverage_by_id[node_id]
        for node_id in target.required_framework_node_ids
    )
    covered_node_ids = tuple(
        item.framework_node_id
        for item in required_coverages
        if item.coverage_state != "uncovered"
    )
    missing_node_ids = tuple(
        item.framework_node_id
        for item in required_coverages
        if item.coverage_state == "uncovered"
    )

    required_upstream = tuple(
        assessments_by_id[dependency_id]
        for dependency_id in target.required_support_target_ids
    )
    satisfied_upstream_ids = tuple(
        item.support_target_id
        for item in required_upstream
        if item.support_state == "potentially_supported"
    )
    unsatisfied_upstream_ids = tuple(
        item.support_target_id
        for item in required_upstream
        if item.support_state != "potentially_supported"
    )

    applicable_issues = tuple(
        issue
        for issue in issues
        if _issue_applies_to_target(issue, target)
    )
    node_attention = any(
        item.attention_required for item in required_coverages
    )
    upstream_blocking_attention = any(
        item.support_state == "attention_required"
        for item in required_upstream
    )
    upstream_warning_attention = any(
        item.attention_required
        and item.support_state != "attention_required"
        for item in required_upstream
    )
    blocking_issue = any(
        issue.issue_level == "blocking" for issue in applicable_issues
    )
    warning_issue = any(
        issue.issue_level == "warning" for issue in applicable_issues
    )
    blocking_attention = (
        node_attention or upstream_blocking_attention or blocking_issue
    )
    attention_required = (
        blocking_attention or warning_issue or upstream_warning_attention
    )

    all_direct_nodes_covered = not missing_node_ids
    all_upstream_satisfied = not unsatisfied_upstream_ids
    any_requirement_satisfied = bool(
        covered_node_ids or satisfied_upstream_ids
    )

    if all_direct_nodes_covered and all_upstream_satisfied:
        support_state = (
            "attention_required"
            if blocking_attention
            else "potentially_supported"
        )
    elif any_requirement_satisfied:
        support_state = "partially_supported"
    else:
        support_state = "not_supported"

    if support_state not in POTENTIAL_SUPPORT_STATES:
        raise CoverageIntegrityError(
            f"Unsupported derived potential-support state: {support_state}."
        )

    issue_codes = {
        code
        for item in required_coverages
        for code in item.issue_codes
    }
    issue_codes.update(issue.code for issue in applicable_issues)
    issue_codes.update(
        code
        for item in required_upstream
        for code in item.issue_codes
    )
    if missing_node_ids:
        issue_codes.add("required_framework_node_uncovered")
    if unsatisfied_upstream_ids:
        issue_codes.add("required_support_target_unsatisfied")
    if any(
        item.support_state == "attention_required"
        or item.attention_required
        for item in required_upstream
    ):
        issue_codes.add("required_support_target_attention_required")
    if node_attention:
        issue_codes.add("required_framework_node_attention_required")

    return PotentialSupportAssessment(
        support_target_id=target.support_target_id,
        name=target.name,
        support_target_type=target.support_target_type,
        support_state=support_state,
        required_framework_node_ids=(
            target.required_framework_node_ids
        ),
        covered_framework_node_ids=covered_node_ids,
        missing_framework_node_ids=missing_node_ids,
        required_support_target_ids=(
            target.required_support_target_ids
        ),
        satisfied_support_target_ids=satisfied_upstream_ids,
        unsatisfied_support_target_ids=unsatisfied_upstream_ids,
        attention_required=attention_required,
        issue_codes=tuple(sorted(issue_codes)),
    )


def _issue_applies_to_target(
    issue: CoverageIssue,
    target: PreliminarySupportTarget,
) -> bool:
    if issue.support_target_id is not None:
        return issue.support_target_id == target.support_target_id
    if issue.framework_node_id is not None:
        return issue.framework_node_id in target.required_framework_node_ids
    return True


def _validate_project_id(project_id: object) -> None:
    if not isinstance(project_id, str) or not project_id.strip():
        raise CoverageValidationError(
            "project_id must be a non-empty string."
        )


def _validate_support_profile(
    profile: object,
) -> tuple[PreliminarySupportTarget, ...]:
    if not isinstance(profile, PreliminarySupportProfile):
        raise CoverageProfileError(
            "support_profile must be a PreliminarySupportProfile."
        )
    if profile.status not in SUPPORT_PROFILE_STATUSES:
        raise CoverageProfileError(
            f"Unsupported support profile status: {profile.status!r}."
        )
    if profile.status != "active":
        raise CoverageProfileError(
            "Only an active Preliminary Support Profile may be assessed."
        )
    if (
        profile.profile_fingerprint
        != calculate_preliminary_support_profile_fingerprint(profile)
    ):
        raise CoverageIntegrityError(
            "Preliminary Support Profile fingerprint does not match content."
        )
    if not isinstance(profile.support_targets, tuple) or not profile.support_targets:
        raise CoverageProfileError(
            "support_profile must contain at least one support target."
        )
    if not all(
        isinstance(item, PreliminarySupportTarget)
        for item in profile.support_targets
    ):
        raise CoverageProfileError(
            "support_targets must contain PreliminarySupportTarget values."
        )

    targets = tuple(sorted(profile.support_targets, key=lambda item: item.order))
    if tuple(item.order for item in targets) != tuple(
        range(1, len(targets) + 1)
    ):
        raise CoverageProfileError(
            "Support target order values must be contiguous from 1."
        )
    if targets != profile.support_targets:
        raise CoverageProfileError(
            "support_targets must already be stored in profile order."
        )

    target_ids = tuple(item.support_target_id for item in targets)
    if len(target_ids) != len(set(target_ids)):
        raise CoverageIntegrityError(
            "Duplicate Preliminary Support Target identity."
        )

    seen: set[str] = set()
    for target in targets:
        _validate_support_target(target)
        if any(
            dependency_id not in seen
            for dependency_id in target.required_support_target_ids
        ):
            raise CoverageReferenceError(
                "Support target dependencies must reference earlier "
                "profile targets."
            )
        seen.add(target.support_target_id)
    return targets


def _validate_support_target(target: PreliminarySupportTarget) -> None:
    if (
        not isinstance(target.support_target_id, str)
        or not target.support_target_id
    ):
        raise CoverageProfileError(
            "support_target_id must be a non-empty string."
        )
    if not isinstance(target.name, str) or not target.name.strip():
        raise CoverageProfileError(
            "Support target name must be a non-empty string."
        )
    if target.support_target_type not in SUPPORT_TARGET_TYPES:
        raise CoverageProfileError(
            "Unsupported support_target_type: "
            f"{target.support_target_type!r}."
        )
    if isinstance(target.order, bool) or not isinstance(target.order, int):
        raise CoverageProfileError(
            "Support target order must be an integer."
        )
    if not isinstance(target.required_framework_node_ids, tuple):
        raise CoverageProfileError(
            "required_framework_node_ids must be a tuple."
        )
    if not target.required_framework_node_ids:
        raise CoverageProfileError(
            "Every support target must require at least one framework node."
        )
    if not all(
        isinstance(item, str) and item
        for item in target.required_framework_node_ids
    ):
        raise CoverageProfileError(
            "required_framework_node_ids must contain non-empty strings."
        )
    if len(target.required_framework_node_ids) != len(
        set(target.required_framework_node_ids)
    ):
        raise CoverageIntegrityError(
            "Duplicate required Framework node in support target."
        )
    if not isinstance(target.required_support_target_ids, tuple):
        raise CoverageProfileError(
            "required_support_target_ids must be a tuple."
        )
    if not all(
        isinstance(item, str) and item
        for item in target.required_support_target_ids
    ):
        raise CoverageProfileError(
            "required_support_target_ids must contain non-empty strings."
        )
    if len(target.required_support_target_ids) != len(
        set(target.required_support_target_ids)
    ):
        raise CoverageIntegrityError(
            "Duplicate required support target dependency."
        )
    if target.support_target_id in target.required_support_target_ids:
        raise CoverageIntegrityError(
            "A support target cannot depend on itself."
        )


def _validate_node_coverages(
    node_coverages: object,
) -> dict[str, FrameworkNodeCoverage]:
    _require_tuple_of(
        node_coverages,
        FrameworkNodeCoverage,
        "node_coverages",
    )
    assert isinstance(node_coverages, tuple)
    if not node_coverages:
        raise CoverageValidationError(
            "node_coverages must contain at least one record."
        )
    result: dict[str, FrameworkNodeCoverage] = {}
    for item in node_coverages:
        _validate_node_coverage(item)
        if item.framework_node_id in result:
            raise CoverageIntegrityError(
                "Duplicate Framework Node Coverage identity: "
                f"{item.framework_node_id}."
            )
        result[item.framework_node_id] = item
    return result


def _validate_node_coverage(item: FrameworkNodeCoverage) -> None:
    if not isinstance(item.framework_node_id, str) or not item.framework_node_id:
        raise CoverageValidationError(
            "Framework Node Coverage must define framework_node_id."
        )
    if item.coverage_state not in FRAMEWORK_NODE_COVERAGE_STATES:
        raise CoverageValidationError(
            f"Unsupported Framework Node Coverage state: {item.coverage_state!r}."
        )
    if not isinstance(item.attention_required, bool):
        raise CoverageValidationError(
            "Framework Node Coverage attention_required must be boolean."
        )
    identifier_fields = (
        item.source_ids,
        item.information_unit_ids,
        item.framework_assignment_candidate_ids,
        item.human_review_decision_ids,
        item.issue_codes,
    )
    if not all(isinstance(values, tuple) for values in identifier_fields):
        raise CoverageValidationError(
            "Framework Node Coverage identifier collections must be tuples."
        )
    if any(len(values) != len(set(values)) for values in identifier_fields):
        raise CoverageIntegrityError(
            "Framework Node Coverage collections must contain unique values."
        )
    if item.eligible_source_count != len(item.source_ids):
        raise CoverageIntegrityError(
            "eligible_source_count does not match source_ids."
        )
    if item.information_unit_count != len(item.information_unit_ids):
        raise CoverageIntegrityError(
            "information_unit_count does not match information_unit_ids."
        )
    if item.assignment_candidate_count > len(
        item.framework_assignment_candidate_ids
    ):
        raise CoverageIntegrityError(
            "assignment_candidate_count exceeds candidate IDs."
        )
    count_fields = (
        item.eligible_source_count,
        item.information_unit_count,
        item.assignment_candidate_count,
        item.confirmed_candidate_count,
        item.unreviewed_candidate_count,
        item.rejected_candidate_count,
        item.ambiguous_candidate_count,
        item.conflicting_candidate_count,
    )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in count_fields
    ):
        raise CoverageValidationError(
            "Framework Node Coverage counts must be non-negative integers."
        )
    if item.confirmed_candidate_count + item.unreviewed_candidate_count > (
        item.assignment_candidate_count
    ):
        raise CoverageIntegrityError(
            "Covering candidate counts exceed assignment_candidate_count."
        )


def _validate_issues(
    project_id: str,
    issues: object,
    *,
    known_node_ids: set[str],
    known_support_target_ids: set[str],
) -> tuple[CoverageIssue, ...]:
    _require_tuple_of(issues, CoverageIssue, "issues")
    assert isinstance(issues, tuple)
    seen: set[tuple[object, ...]] = set()
    for issue in issues:
        if issue.project_id != project_id:
            raise CoverageReferenceError(
                "Coverage Issue belongs to another project."
            )
        if not isinstance(issue.code, str) or not issue.code:
            raise CoverageValidationError(
                "Coverage Issue code must be a non-empty string."
            )
        if issue.issue_level not in COVERAGE_ISSUE_LEVELS:
            raise CoverageValidationError(
                f"Unsupported Coverage Issue level: {issue.issue_level!r}."
            )
        if (
            issue.framework_node_id is not None
            and issue.framework_node_id not in known_node_ids
        ):
            raise CoverageReferenceError(
                "Coverage Issue references an unknown Framework node: "
                f"{issue.framework_node_id}."
            )
        if (
            issue.support_target_id is not None
            and issue.support_target_id not in known_support_target_ids
        ):
            raise CoverageReferenceError(
                "Coverage Issue references an unknown support target: "
                f"{issue.support_target_id}."
            )
        identity = (
            issue.code,
            issue.issue_level,
            issue.framework_node_id,
            issue.support_target_id,
            issue.source_id,
            issue.information_unit_id,
            issue.framework_assignment_candidate_id,
            issue.human_review_decision_id,
        )
        if identity in seen:
            raise CoverageIntegrityError(
                "Duplicate Coverage Issue identity in support assessment."
            )
        seen.add(identity)
    return tuple(
        sorted(
            issues,
            key=lambda item: (
                item.support_target_id or "",
                item.framework_node_id or "",
                item.issue_level,
                item.code,
                item.message,
            ),
        )
    )


def _require_tuple_of(
    value: object,
    data_type: type,
    label: str,
) -> None:
    if not isinstance(value, tuple) or not all(
        isinstance(item, data_type) for item in value
    ):
        raise CoverageValidationError(
            f"{label} must be a tuple of {data_type.__name__} values."
        )
