"""Immutable data types for P6 coverage and potential-support assessment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


FRAMEWORK_NODE_COVERAGE_STATES = frozenset(
    {"uncovered", "candidate_covered", "reviewed_candidate_covered"}
)
FRAMEWORK_LEVEL_COVERAGE_STATES = frozenset(
    {"uncovered", "partially_covered", "covered"}
)
PROJECT_COVERAGE_STATES = frozenset(
    {"uncovered", "partially_covered", "covered", "attention_required"}
)
POTENTIAL_SUPPORT_STATES = frozenset(
    {"not_supported", "partially_supported", "potentially_supported", "attention_required"}
)
COVERAGE_ISSUE_LEVELS = frozenset({"warning", "blocking"})
COVERAGE_EVIDENCE_STATES = frozenset(
    {
        "eligible_unreviewed",
        "eligible_confirmed",
        "excluded_rejected",
        "excluded_request_changes",
        "excluded_unassigned",
        "excluded_ambiguous",
        "excluded_conflict",
        "excluded_source",
        "excluded_invalidated",
        "excluded_invalid_reference",
    }
)
APPROVED_READINESS_STATUSES = frozenset({"not_available"})
SUPPORT_TARGET_TYPES = frozenset({"model", "submodel"})
SUPPORT_PROFILE_STATUSES = frozenset({"draft", "active", "retired"})


@dataclass(frozen=True, slots=True)
class PreliminarySupportTarget:
    """One versioned dependency rule for a potential model scope."""

    support_target_id: str
    name: str
    support_target_type: str
    order: int
    required_framework_node_ids: tuple[str, ...]
    required_support_target_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreliminarySupportProfile:
    """Validated versioned rules for deriving potential model support."""

    schema_version: str
    profile_id: str
    profile_version: str
    name: str
    status: str
    framework_template_id: str
    framework_template_version: str
    support_targets: tuple[PreliminarySupportTarget, ...]
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class CoverageIssue:
    """One deterministic P6 warning or blocking diagnostic."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    source_id: str | None = None
    information_unit_id: str | None = None
    framework_node_id: str | None = None
    framework_assignment_candidate_id: str | None = None
    human_review_decision_id: str | None = None
    support_target_id: str | None = None


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentCoverageEvidence:
    """Resolved P6 interpretation of one Framework Assignment Candidate."""

    project_id: str
    source_id: str
    information_unit_id: str
    framework_assignment_candidate_id: str
    evidence_state: str
    framework_node_ids: tuple[str, ...]
    human_review_decision_id: str | None
    attention_required: bool
    issue_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrameworkNodeCoverage:
    """Derived preliminary coverage for one framework mapping target."""

    framework_node_id: str
    mapping_key: str
    node_name: str
    level_node_id: str
    coverage_state: str
    attention_required: bool
    eligible_source_count: int
    information_unit_count: int
    assignment_candidate_count: int
    confirmed_candidate_count: int
    unreviewed_candidate_count: int
    rejected_candidate_count: int
    ambiguous_candidate_count: int
    conflicting_candidate_count: int
    source_ids: tuple[str, ...]
    information_unit_ids: tuple[str, ...]
    framework_assignment_candidate_ids: tuple[str, ...]
    human_review_decision_ids: tuple[str, ...]
    issue_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrameworkLevelCoverage:
    """Derived preliminary coverage for one framework level."""

    level_node_id: str
    level_name: str
    coverage_state: str
    covered_node_count: int
    total_node_count: int
    candidate_covered_node_count: int
    reviewed_candidate_covered_node_count: int
    attention_node_count: int
    covered_node_ids: tuple[str, ...]
    uncovered_node_ids: tuple[str, ...]
    attention_node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PotentialSupportAssessment:
    """Derived potential support for one profile target."""

    support_target_id: str
    name: str
    support_target_type: str
    support_state: str
    required_framework_node_ids: tuple[str, ...]
    covered_framework_node_ids: tuple[str, ...]
    missing_framework_node_ids: tuple[str, ...]
    required_support_target_ids: tuple[str, ...]
    satisfied_support_target_ids: tuple[str, ...]
    unsatisfied_support_target_ids: tuple[str, ...]
    attention_required: bool
    issue_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectCoverageAssessment:
    """Complete regenerable P6 project assessment."""

    project_id: str
    framework_template_id: str
    framework_template_version: str
    support_profile_id: str
    support_profile_version: str
    project_coverage_state: str
    node_coverages: tuple[FrameworkNodeCoverage, ...]
    level_coverages: tuple[FrameworkLevelCoverage, ...]
    support_assessments: tuple[PotentialSupportAssessment, ...]
    approved_readiness_status: str
    approved_readiness_available_from_phase: str
    assessment_algorithm_id: str
    assessment_algorithm_version: str
    assessment_input_fingerprint: str
    issues: tuple[CoverageIssue, ...]