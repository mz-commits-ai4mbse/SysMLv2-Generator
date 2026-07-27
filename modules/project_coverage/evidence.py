"""Resolve P6 eligibility and exact Human Review state for assignment evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from modules.framework import mapping_target_ids, validate_framework_template
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
)
from modules.framework_assignment.types import (
    FRAMEWORK_ASSIGNMENT_STATUSES,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentIssue,
)
from modules.human_review.types import HumanReviewDecision
from modules.information_units.types import InformationUnit
from modules.project_processing.types import (
    ProcessingArtifactLifecycle,
    SourceProcessingSummary,
)
from modules.project_sources.types import SourceManifest

from .errors import (
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
)
from .types import (
    COVERAGE_EVIDENCE_STATES,
    FrameworkAssignmentCoverageEvidence,
)


FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE = "framework_assignment_candidate"


def calculate_framework_assignment_reference_validation_fingerprint(
    result: FrameworkAssignmentReferenceValidationResult,
) -> str:
    """Return a deterministic fingerprint for one P4 validation result."""

    _require_validation_result(result)
    canonical = {
        "project_id": result.project_id,
        "framework_assignment_candidate_id": (
            result.framework_assignment_candidate_id
        ),
        "checked_proposal_count": result.checked_proposal_count,
        "references_valid": result.references_valid,
        "issues": [
            _canonical_assignment_issue(issue)
            for issue in sorted(
                result.issues,
                key=lambda item: (
                    item.issue_level,
                    item.code,
                    item.message,
                    "" if item.information_unit_id is None else item.information_unit_id,
                    ""
                    if item.framework_assignment_candidate_id is None
                    else item.framework_assignment_candidate_id,
                    "" if item.persona_id is None else item.persona_id,
                    "" if item.agent_id is None else item.agent_id,
                    -1 if item.persona_run_index is None else item.persona_run_index,
                    "" if item.path is None else str(item.path),
                ),
            )
        ],
    }
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_latest_exact_framework_assignment_review(
    candidate: FrameworkAssignmentCandidate,
    validation_result: FrameworkAssignmentReferenceValidationResult,
    decisions: tuple[HumanReviewDecision, ...],
) -> HumanReviewDecision | None:
    """Return the latest decision bound to the exact current candidate snapshot."""

    if not isinstance(candidate, FrameworkAssignmentCandidate):
        raise CoverageValidationError(
            "candidate must be a FrameworkAssignmentCandidate."
        )
    _require_validation_result(validation_result)
    _require_tuple_of(
        decisions,
        HumanReviewDecision,
        "decisions",
    )
    if validation_result.project_id != candidate.project_id:
        raise CoverageReferenceError(
            "Candidate and reference-validation result disagree on project_id."
        )
    if (
        validation_result.framework_assignment_candidate_id
        != candidate.framework_assignment_candidate_id
    ):
        raise CoverageReferenceError(
            "Candidate and reference-validation result disagree on candidate ID."
        )

    decision_ids: set[str] = set()
    relevant: list[HumanReviewDecision] = []
    expected_validation_fingerprint = (
        calculate_framework_assignment_reference_validation_fingerprint(
            validation_result
        )
    )
    expected_validation_status = (
        "valid" if validation_result.references_valid else "invalid"
    )

    for decision in decisions:
        if decision.human_review_decision_id in decision_ids:
            raise CoverageIntegrityError(
                "Duplicate Human Review Decision identity: "
                f"{decision.human_review_decision_id}."
            )
        decision_ids.add(decision.human_review_decision_id)
        if decision.project_id != candidate.project_id:
            raise CoverageReferenceError(
                "Human Review Decision belongs to another project: "
                f"{decision.human_review_decision_id}."
            )
        target = decision.target
        if target.target_type != "framework_assignment_candidate":
            continue
        if target.target_id != candidate.framework_assignment_candidate_id:
            continue
        if target.target_content_fingerprint != candidate.content_fingerprint:
            continue
        if (
            target.reference_validation_fingerprint
            != expected_validation_fingerprint
        ):
            continue
        if target.reference_validation_status != expected_validation_status:
            continue
        relevant.append(decision)

    if not relevant:
        return None
    return max(
        relevant,
        key=lambda item: (
            item.decided_at,
            item.human_review_decision_id,
        ),
    )


def derive_framework_assignment_coverage_evidence(
    project_id: str,
    *,
    framework_template: dict[str, Any],
    source_manifests: tuple[SourceManifest, ...],
    source_processing_summaries: tuple[SourceProcessingSummary, ...],
    information_units: tuple[InformationUnit, ...],
    candidates: tuple[FrameworkAssignmentCandidate, ...],
    reference_validation_results: tuple[
        FrameworkAssignmentReferenceValidationResult,
        ...,
    ],
    human_review_decisions: tuple[HumanReviewDecision, ...],
    artifact_lifecycles: tuple[ProcessingArtifactLifecycle, ...] = (),
) -> tuple[FrameworkAssignmentCoverageEvidence, ...]:
    """Resolve one deterministic P6 evidence record per assignment candidate."""

    if not isinstance(project_id, str) or not project_id:
        raise CoverageValidationError("project_id must be a non-empty string.")
    if not isinstance(framework_template, dict):
        raise CoverageValidationError(
            "framework_template must be a dictionary."
        )
    try:
        validate_framework_template(framework_template)
        permitted_nodes = mapping_target_ids(framework_template)
    except Exception as exc:
        raise CoverageValidationError(
            "framework_template violates the framework contract."
        ) from exc

    _require_tuple_of(source_manifests, SourceManifest, "source_manifests")
    _require_tuple_of(
        source_processing_summaries,
        SourceProcessingSummary,
        "source_processing_summaries",
    )
    _require_tuple_of(information_units, InformationUnit, "information_units")
    _require_tuple_of(candidates, FrameworkAssignmentCandidate, "candidates")
    _require_tuple_of(
        reference_validation_results,
        FrameworkAssignmentReferenceValidationResult,
        "reference_validation_results",
    )
    _require_tuple_of(
        human_review_decisions,
        HumanReviewDecision,
        "human_review_decisions",
    )
    _require_tuple_of(
        artifact_lifecycles,
        ProcessingArtifactLifecycle,
        "artifact_lifecycles",
    )

    sources = _index_unique(
        source_manifests,
        key="source_id",
        label="Source Manifest",
        project_id=project_id,
    )
    summaries = _index_unique(
        source_processing_summaries,
        key="source_id",
        label="Source Processing Summary",
        project_id=project_id,
    )
    units = _index_unique(
        information_units,
        key="information_unit_id",
        label="Information Unit",
        project_id=project_id,
    )
    candidates_by_id = _index_unique(
        candidates,
        key="framework_assignment_candidate_id",
        label="Framework Assignment Candidate",
        project_id=project_id,
    )
    validations = _index_unique(
        reference_validation_results,
        key="framework_assignment_candidate_id",
        label="Framework Assignment Reference Validation Result",
        project_id=project_id,
    )
    _validate_decisions(project_id, human_review_decisions)
    lifecycle_states = _candidate_lifecycle_states(
        project_id,
        artifact_lifecycles,
    )

    unknown_summary_sources = set(summaries) - set(sources)
    if unknown_summary_sources:
        raise CoverageReferenceError(
            "Source Processing Summaries reference unknown sources: "
            + ", ".join(sorted(unknown_summary_sources))
            + "."
        )
    unknown_validation_candidates = set(validations) - set(candidates_by_id)
    if unknown_validation_candidates:
        raise CoverageReferenceError(
            "Reference-validation results reference unknown candidates: "
            + ", ".join(sorted(unknown_validation_candidates))
            + "."
        )

    evidence = []
    for candidate_id in sorted(candidates_by_id):
        candidate = candidates_by_id[candidate_id]
        evidence.append(
            _resolve_candidate(
                candidate,
                project_id=project_id,
                template_id=framework_template["template_id"],
                template_version=framework_template["template_version"],
                permitted_nodes=permitted_nodes,
                sources=sources,
                summaries=summaries,
                units=units,
                validation_result=validations.get(candidate_id),
                decisions=human_review_decisions,
                lifecycle_state=lifecycle_states.get(candidate_id),
            )
        )
    return tuple(evidence)


def _resolve_candidate(
    candidate: FrameworkAssignmentCandidate,
    *,
    project_id: str,
    template_id: str,
    template_version: str,
    permitted_nodes: set[str],
    sources: Mapping[str, SourceManifest],
    summaries: Mapping[str, SourceProcessingSummary],
    units: Mapping[str, InformationUnit],
    validation_result: FrameworkAssignmentReferenceValidationResult | None,
    decisions: tuple[HumanReviewDecision, ...],
    lifecycle_state: str | None,
) -> FrameworkAssignmentCoverageEvidence:
    node_ids = tuple(
        sorted({proposal.framework_node_id for proposal in candidate.proposals})
    )
    issues: set[str] = set()

    unit = units.get(candidate.information_unit_id)
    source = sources.get(candidate.source_id)
    summary = summaries.get(candidate.source_id)

    if source is None:
        issues.add("unknown_source")
    if unit is None:
        issues.add("unknown_information_unit")
    if summary is None:
        issues.add("missing_source_processing_summary")
    if unit is not None:
        if unit.source_id != candidate.source_id:
            issues.add("candidate_information_unit_source_mismatch")
        if unit.source_projection_id != candidate.source_projection_id:
            issues.add("candidate_information_unit_projection_mismatch")
    if candidate.framework_template_id != template_id:
        issues.add("framework_template_id_mismatch")
    if candidate.framework_template_version != template_version:
        issues.add("framework_template_version_mismatch")
    if set(node_ids) - permitted_nodes:
        issues.add("unknown_framework_node")
    if candidate.assignment_status not in FRAMEWORK_ASSIGNMENT_STATUSES:
        issues.add("invalid_assignment_status")
    if validation_result is None:
        issues.add("missing_reference_validation")
    elif not validation_result.references_valid:
        issues.add("invalid_framework_assignment_references")
        issues.update(issue.code for issue in validation_result.issues)
    if lifecycle_state in {"invalidated", "superseded"}:
        return _evidence(
            candidate,
            "excluded_invalidated",
            node_ids,
            None,
            True,
            issues | {"framework_assignment_candidate_not_active"},
        )

    structural_issues = {
        "unknown_source",
        "unknown_information_unit",
        "missing_source_processing_summary",
        "candidate_information_unit_source_mismatch",
        "candidate_information_unit_projection_mismatch",
        "framework_template_id_mismatch",
        "framework_template_version_mismatch",
        "unknown_framework_node",
        "invalid_assignment_status",
        "missing_reference_validation",
        "invalid_framework_assignment_references",
    }
    if issues & structural_issues:
        return _evidence(
            candidate,
            "excluded_invalid_reference",
            node_ids,
            None,
            True,
            issues,
        )

    assert source is not None
    assert summary is not None
    assert validation_result is not None

    if (
        source.source_role != "engineering_source"
        or summary.processing_disposition != "in_scope"
    ):
        return _evidence(
            candidate,
            "excluded_source",
            node_ids,
            None,
            False,
            {"source_not_coverage_eligible"},
        )

    if candidate.assignment_status == "unassigned":
        return _evidence(
            candidate,
            "excluded_unassigned",
            node_ids,
            None,
            False,
            {"framework_assignment_unassigned"},
        )
    if candidate.assignment_status == "ambiguous":
        return _evidence(
            candidate,
            "excluded_ambiguous",
            node_ids,
            None,
            True,
            {"framework_assignment_ambiguous"},
        )
    if candidate.assignment_status == "conflict":
        return _evidence(
            candidate,
            "excluded_conflict",
            node_ids,
            None,
            True,
            {"framework_assignment_conflict"},
        )

    exact = resolve_latest_exact_framework_assignment_review(
        candidate,
        validation_result,
        decisions,
    )
    targeted_decisions = tuple(
        decision
        for decision in decisions
        if decision.target.target_type == "framework_assignment_candidate"
        and decision.target.target_id
        == candidate.framework_assignment_candidate_id
    )
    if exact is None:
        stale = bool(targeted_decisions)
        return _evidence(
            candidate,
            "eligible_unreviewed",
            node_ids,
            None,
            stale,
            {"stale_human_review_binding"} if stale else set(),
        )
    if exact.decision == "confirm":
        return _evidence(
            candidate,
            "eligible_confirmed",
            node_ids,
            exact.human_review_decision_id,
            False,
            set(),
        )
    if exact.decision == "reject":
        return _evidence(
            candidate,
            "excluded_rejected",
            node_ids,
            exact.human_review_decision_id,
            False,
            {"framework_assignment_rejected"},
        )
    if exact.decision == "request_changes":
        return _evidence(
            candidate,
            "excluded_request_changes",
            node_ids,
            exact.human_review_decision_id,
            True,
            {"framework_assignment_changes_requested"},
        )
    raise CoverageIntegrityError(
        "Unsupported Human Review decision: "
        f"{exact.human_review_decision_id}/{exact.decision}."
    )


def _evidence(
    candidate: FrameworkAssignmentCandidate,
    state: str,
    node_ids: tuple[str, ...],
    decision_id: str | None,
    attention: bool,
    issues: set[str],
) -> FrameworkAssignmentCoverageEvidence:
    if state not in COVERAGE_EVIDENCE_STATES:
        raise CoverageIntegrityError(
            f"Unsupported coverage evidence state: {state}."
        )
    return FrameworkAssignmentCoverageEvidence(
        project_id=candidate.project_id,
        source_id=candidate.source_id,
        information_unit_id=candidate.information_unit_id,
        framework_assignment_candidate_id=(
            candidate.framework_assignment_candidate_id
        ),
        evidence_state=state,
        framework_node_ids=node_ids,
        human_review_decision_id=decision_id,
        attention_required=attention,
        issue_codes=tuple(sorted(issues)),
    )


def _candidate_lifecycle_states(
    project_id: str,
    lifecycles: tuple[ProcessingArtifactLifecycle, ...],
) -> dict[str, str]:
    states: dict[str, str] = {}
    identities: dict[str, tuple[str, str]] = {}
    for lifecycle in lifecycles:
        reference = lifecycle.artifact_reference
        if reference.artifact_type != FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE:
            continue
        candidate_id = reference.artifact_id
        identity = (
            reference.content_fingerprint,
            reference.repository_relative_path,
        )
        previous_identity = identities.get(candidate_id)
        if previous_identity is not None and previous_identity != identity:
            raise CoverageIntegrityError(
                "Framework Assignment Candidate artifact identity is "
                f"inconsistent: {candidate_id}."
            )
        previous_state = states.get(candidate_id)
        if previous_state is not None and previous_state != lifecycle.lifecycle_state:
            raise CoverageIntegrityError(
                "Framework Assignment Candidate has multiple lifecycle states: "
                f"{candidate_id}."
            )
        identities[candidate_id] = identity
        states[candidate_id] = lifecycle.lifecycle_state
    return states


def _validate_decisions(
    project_id: str,
    decisions: tuple[HumanReviewDecision, ...],
) -> None:
    seen: set[str] = set()
    for decision in decisions:
        if decision.project_id != project_id:
            raise CoverageReferenceError(
                "Human Review Decision belongs to another project: "
                f"{decision.human_review_decision_id}."
            )
        if decision.human_review_decision_id in seen:
            raise CoverageIntegrityError(
                "Duplicate Human Review Decision identity: "
                f"{decision.human_review_decision_id}."
            )
        seen.add(decision.human_review_decision_id)


def _index_unique(
    values: tuple[Any, ...],
    *,
    key: str,
    label: str,
    project_id: str,
) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for item in values:
        item_project_id = getattr(item, "project_id", None)
        if item_project_id != project_id:
            raise CoverageReferenceError(
                f"{label} belongs to another project: {item_project_id!r}."
            )
        identity = getattr(item, key)
        if identity in indexed:
            raise CoverageIntegrityError(
                f"Duplicate {label} identity: {identity}."
            )
        indexed[identity] = item
    return indexed


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


def _require_validation_result(
    result: FrameworkAssignmentReferenceValidationResult,
) -> None:
    if not isinstance(result, FrameworkAssignmentReferenceValidationResult):
        raise CoverageValidationError(
            "result must be a FrameworkAssignmentReferenceValidationResult."
        )
    if (
        isinstance(result.checked_proposal_count, bool)
        or not isinstance(result.checked_proposal_count, int)
        or result.checked_proposal_count < 0
    ):
        raise CoverageValidationError(
            "checked_proposal_count must be a non-negative integer."
        )
    if not isinstance(result.references_valid, bool):
        raise CoverageValidationError("references_valid must be boolean.")
    _require_tuple_of(result.issues, FrameworkAssignmentIssue, "result.issues")
    if result.references_valid and any(
        issue.issue_level == "blocking" for issue in result.issues
    ):
        raise CoverageIntegrityError(
            "A reference-valid result cannot contain blocking issues."
        )
    if not result.references_valid and not any(
        issue.issue_level == "blocking" for issue in result.issues
    ):
        raise CoverageIntegrityError(
            "A reference-invalid result must contain a blocking issue."
        )


def _canonical_assignment_issue(issue: FrameworkAssignmentIssue) -> dict[str, Any]:
    if not isinstance(issue, FrameworkAssignmentIssue):
        raise CoverageValidationError(
            "Validation issues must be FrameworkAssignmentIssue values."
        )
    return {
        "project_id": issue.project_id,
        "code": issue.code,
        "message": issue.message,
        "issue_level": issue.issue_level,
        "path": None if issue.path is None else str(Path(issue.path)),
        "information_unit_id": issue.information_unit_id,
        "framework_assignment_candidate_id": (
            issue.framework_assignment_candidate_id
        ),
        "persona_id": issue.persona_id,
        "agent_id": issue.agent_id,
        "persona_run_index": issue.persona_run_index,
    }