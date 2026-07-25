"""Derive deterministic source-level and project-level processing summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)
from modules.project_sources.manifest import validate_source_manifest
from modules.project_workspace.identifiers import is_valid_project_id

from .artifact_lifecycle import (
    SourceDispositionImpact,
    derive_effective_source_dispositions,
    derive_processing_artifact_lifecycles,
    derive_source_disposition_impacts,
)
from .errors import (
    ProcessingIntegrityError,
    ProcessingReferenceError,
    ProcessingValidationError,
    ProjectProcessingError,
)
from .history import derive_processing_run_state, validate_processing_run_history
from .run_lifecycle import derive_project_run_states
from .types import (
    DerivedProcessingRunState,
    ProcessingArtifactLifecycle,
    ProcessingDecision,
    ProcessingIssue,
    ProcessingRunHistory,
    ProcessingScanResult,
    ProjectProcessingSummary,
    SourceProcessingSummary,
)


@dataclass(frozen=True, slots=True)
class _AggregationContext:
    project_id: str
    sources: tuple[SourceManifest, ...]
    histories: tuple[ProcessingRunHistory, ...]
    decisions: tuple[ProcessingDecision, ...]
    run_states: tuple[DerivedProcessingRunState, ...]
    lifecycles: tuple[ProcessingArtifactLifecycle, ...]
    impacts: tuple[SourceDispositionImpact, ...]
    issues: tuple[ProcessingIssue, ...]


def derive_source_processing_summaries(
    project_id: str,
    source_scan: object,
    processing_scan: object,
) -> tuple[SourceProcessingSummary, ...]:
    """Return one deterministic processing summary per registered source."""

    context = _build_context(
        project_id,
        source_scan,
        processing_scan,
    )
    return _derive_source_summaries(context)


def derive_project_processing_summary(
    project_id: str,
    source_scan: object,
    processing_scan: object,
) -> ProjectProcessingSummary:
    """Derive the canonical project-level Processing State projection."""

    context = _build_context(
        project_id,
        source_scan,
        processing_scan,
    )
    summaries = _derive_source_summaries(context)

    total_sources = len(summaries)
    in_scope_sources = sum(
        summary.processing_disposition == "in_scope"
        for summary in summaries
    )
    context_only_sources = sum(
        summary.processing_disposition == "context_only"
        for summary in summaries
    )
    out_of_scope_sources = sum(
        summary.processing_disposition == "out_of_scope"
        for summary in summaries
    )

    relevant = tuple(
        summary
        for summary in summaries
        if summary.processing_disposition != "out_of_scope"
    )

    classifications = {
        summary.source_id: _classify_source(summary)
        for summary in relevant
    }

    not_started_sources = sum(
        value == "not_started"
        for value in classifications.values()
    )
    running_sources = sum(
        value == "running"
        for value in classifications.values()
    )
    awaiting_review_sources = sum(
        value == "awaiting_review"
        for value in classifications.values()
    )
    blocked_sources = sum(
        value == "blocked"
        for value in classifications.values()
    )
    failed_sources = sum(
        value == "failed"
        for value in classifications.values()
    )
    completed_sources = sum(
        value == "completed"
        for value in classifications.values()
    )

    has_project_blocking_issue = any(
        issue.issue_level == "blocking"
        and issue.source_id is None
        and issue.processing_run_id is None
        for issue in context.issues
    )

    project_state = _derive_project_state(
        total_sources=total_sources,
        relevant_sources=len(relevant),
        not_started_sources=not_started_sources,
        running_sources=running_sources,
        awaiting_review_sources=awaiting_review_sources,
        blocked_sources=blocked_sources,
        failed_sources=failed_sources,
        completed_sources=completed_sources,
        has_project_blocking_issue=has_project_blocking_issue,
    )

    superseded_runs = sum(
        state.run_state == "superseded"
        or state.superseded_by_run_id is not None
        for state in context.run_states
    )
    invalidated_artifacts = sum(
        lifecycle.lifecycle_state == "invalidated"
        for lifecycle in context.lifecycles
    )

    return ProjectProcessingSummary(
        project_id=context.project_id,
        project_state=project_state,
        total_sources=total_sources,
        in_scope_sources=in_scope_sources,
        context_only_sources=context_only_sources,
        out_of_scope_sources=out_of_scope_sources,
        not_started_sources=not_started_sources,
        running_sources=running_sources,
        awaiting_review_sources=awaiting_review_sources,
        blocked_sources=blocked_sources,
        failed_sources=failed_sources,
        completed_sources=completed_sources,
        superseded_runs=superseded_runs,
        invalidated_artifacts=invalidated_artifacts,
        source_summaries=summaries,
        issues=context.issues,
    )


def _build_context(
    project_id: str,
    source_scan: object,
    processing_scan: object,
) -> _AggregationContext:
    validated_project_id = _validate_project_id(project_id)
    validated_source_scan = _validate_source_scan(
        source_scan,
        expected_project_id=validated_project_id,
    )
    validated_processing_scan = _validate_processing_scan(
        processing_scan,
        expected_project_id=validated_project_id,
    )

    sources = tuple(
        sorted(
            validated_source_scan.valid_sources,
            key=lambda source: source.source_id,
        )
    )
    source_by_id = _source_index(sources)

    histories = tuple(
        validate_processing_run_history(history)
        for history in validated_processing_scan.run_histories
    )
    decisions = validated_processing_scan.decisions

    _validate_history_references(
        validated_project_id,
        histories,
        source_by_id,
    )
    _validate_decision_references(
        validated_project_id,
        decisions,
        source_by_id,
    )

    issues = [
        _source_issue_to_processing_issue(issue)
        for issue in validated_source_scan.source_issues
    ]
    issues.extend(validated_processing_scan.issues)

    run_states: tuple[DerivedProcessingRunState, ...]
    try:
        run_states = derive_project_run_states(histories)
    except ProjectProcessingError as exc:
        issues.append(
            _derived_issue(
                validated_project_id,
                code="run_state_derivation_failed",
                message=str(exc),
            )
        )
        run_states = tuple(
            sorted(
                (
                    derive_processing_run_state(history)
                    for history in histories
                ),
                key=lambda state: state.processing_run_id,
            )
        )

    lifecycles: tuple[ProcessingArtifactLifecycle, ...]
    try:
        lifecycles = derive_processing_artifact_lifecycles(histories)
    except ProjectProcessingError as exc:
        issues.append(
            _derived_issue(
                validated_project_id,
                code="artifact_lifecycle_derivation_failed",
                message=str(exc),
            )
        )
        lifecycles = ()

    impacts: tuple[SourceDispositionImpact, ...]
    try:
        impacts = derive_source_disposition_impacts(
            histories,
            decisions,
        )
    except ProjectProcessingError as exc:
        issues.append(
            _derived_issue(
                validated_project_id,
                code="source_disposition_impact_derivation_failed",
                message=str(exc),
            )
        )
        impacts = ()

    issues.extend(
        _state_issues(
            validated_project_id,
            run_states,
            histories,
        )
    )
    issues.extend(
        _multiple_current_run_issues(
            validated_project_id,
            source_by_id,
            run_states,
        )
    )
    issues.extend(
        _disposition_issues(
            validated_project_id,
            sources,
            histories,
            decisions,
            run_states,
            impacts,
        )
    )
    issues.extend(
        _artifact_source_issues(
            validated_project_id,
            histories,
        )
    )

    normalized_issues = _deduplicate_and_sort_issues(issues)

    return _AggregationContext(
        project_id=validated_project_id,
        sources=sources,
        histories=histories,
        decisions=decisions,
        run_states=run_states,
        lifecycles=lifecycles,
        impacts=impacts,
        issues=normalized_issues,
    )


def _derive_source_summaries(
    context: _AggregationContext,
) -> tuple[SourceProcessingSummary, ...]:
    effective_decisions = _effective_decisions_or_empty(
        context.project_id,
        context.decisions,
        context.issues,
    )
    states_by_source: dict[str, list[DerivedProcessingRunState]] = {}
    history_by_run_id = {
        history.manifest.processing_run_id: history
        for history in context.histories
    }

    for state in context.run_states:
        states_by_source.setdefault(state.source_id, []).append(state)

    invalidated_by_source = _invalidated_artifact_counts(
        context.histories,
        context.lifecycles,
    )
    issues_by_source = _issues_by_source(
        context.issues,
        history_by_run_id,
    )

    summaries = []
    for source in context.sources:
        disposition = _effective_disposition(
            source,
            effective_decisions.get(source.source_id),
        )
        states = tuple(
            sorted(
                states_by_source.get(source.source_id, ()),
                key=lambda state: state.processing_run_id,
            )
        )
        current_candidates = tuple(
            state
            for state in states
            if state.run_state != "superseded"
            and state.superseded_by_run_id is None
        )
        current = (
            current_candidates[0]
            if len(current_candidates) == 1
            else None
        )
        source_issues = issues_by_source.get(source.source_id, ())

        blocking_codes = tuple(
            sorted(
                {
                    issue.code
                    for issue in source_issues
                    if issue.issue_level == "blocking"
                }
            )
        )
        failure_codes = tuple(
            sorted(
                {
                    current.failure_reason
                    for _ in (0,)
                    if current is not None
                    and current.failure_reason is not None
                }
            )
        )

        superseded_run_ids = tuple(
            state.processing_run_id
            for state in states
            if state.run_state == "superseded"
            or state.superseded_by_run_id is not None
        )

        summaries.append(
            SourceProcessingSummary(
                project_id=context.project_id,
                source_id=source.source_id,
                processing_disposition=disposition,
                current_processing_run_id=(
                    current.processing_run_id
                    if current is not None
                    else None
                ),
                run_state=(
                    current.run_state
                    if current is not None
                    else None
                ),
                processing_stage=(
                    current.processing_stage
                    if current is not None
                    else None
                ),
                latest_attempt_id=(
                    current.latest_attempt_id
                    if current is not None
                    else None
                ),
                blocking_issue_codes=blocking_codes,
                failure_issue_codes=failure_codes,
                pending_review=(
                    current.pending_review
                    if current is not None
                    else False
                ),
                superseded_run_ids=superseded_run_ids,
                invalidated_artifact_count=(
                    invalidated_by_source.get(source.source_id, 0)
                ),
            )
        )

    return tuple(summaries)


def _effective_decisions_or_empty(
    project_id: str,
    decisions: tuple[ProcessingDecision, ...],
    issues: tuple[ProcessingIssue, ...],
) -> dict[str, ProcessingDecision]:
    if any(
        issue.code == "source_disposition_impact_derivation_failed"
        for issue in issues
    ):
        try:
            return derive_effective_source_dispositions(decisions)
        except ProjectProcessingError:
            return {}

    try:
        return derive_effective_source_dispositions(decisions)
    except ProjectProcessingError:
        return {}


def _effective_disposition(
    source: SourceManifest,
    decision: ProcessingDecision | None,
) -> str:
    default = (
        "in_scope"
        if source.source_role == ENGINEERING_SOURCE_ROLE
        else "context_only"
    )

    if decision is None or decision.disposition == "in_scope":
        return default

    return decision.disposition


def _classify_source(summary: SourceProcessingSummary) -> str:
    if summary.failure_issue_codes or summary.run_state == "failed":
        return "failed"
    if summary.blocking_issue_codes:
        return "blocked"
    if summary.pending_review or summary.run_state == "awaiting_review":
        return "awaiting_review"
    if summary.run_state == "running":
        return "running"
    if summary.run_state == "completed":
        return "completed"
    return "not_started"


def _derive_project_state(
    *,
    total_sources: int,
    relevant_sources: int,
    not_started_sources: int,
    running_sources: int,
    awaiting_review_sources: int,
    blocked_sources: int,
    failed_sources: int,
    completed_sources: int,
    has_project_blocking_issue: bool,
) -> str:
    if has_project_blocking_issue:
        return "attention_required"
    if total_sources == 0:
        return "empty"
    if blocked_sources or failed_sources:
        return "attention_required"
    if awaiting_review_sources:
        return "awaiting_review"
    if running_sources:
        return "in_progress"
    if relevant_sources == 0:
        return "processed"
    if completed_sources == relevant_sources:
        return "processed"
    if completed_sources:
        return "partially_processed"
    if not_started_sources == relevant_sources:
        return "not_started"
    return "attention_required"


def _validate_project_id(value: object) -> str:
    if not is_valid_project_id(value):
        raise ProcessingValidationError(
            "project_id must be a string containing exactly six digits."
        )
    return value


def _validate_source_scan(
    value: object,
    *,
    expected_project_id: str,
) -> SourceScanResult:
    if not isinstance(value, SourceScanResult):
        raise ProcessingValidationError(
            "source_scan must be a SourceScanResult."
        )
    if not isinstance(value.valid_sources, tuple):
        raise ProcessingValidationError(
            "SourceScanResult.valid_sources must be a tuple."
        )
    if not isinstance(value.source_issues, tuple):
        raise ProcessingValidationError(
            "SourceScanResult.source_issues must be a tuple."
        )

    for source in value.valid_sources:
        try:
            validate_source_manifest(
                source,
                expected_project_id=expected_project_id,
                expected_source_id=source.source_id,
            )
        except Exception as exc:
            raise ProcessingValidationError(
                "SourceScanResult contains an invalid Source Manifest."
            ) from exc

    for issue in value.source_issues:
        if not isinstance(issue, SourceIssue):
            raise ProcessingValidationError(
                "SourceScanResult contains an invalid SourceIssue."
            )
        if issue.project_id != expected_project_id:
            raise ProcessingReferenceError(
                "SourceIssue project_id does not match the project."
            )

    return value


def _validate_processing_scan(
    value: object,
    *,
    expected_project_id: str,
) -> ProcessingScanResult:
    if not isinstance(value, ProcessingScanResult):
        raise ProcessingValidationError(
            "processing_scan must be a ProcessingScanResult."
        )
    if not isinstance(value.run_histories, tuple):
        raise ProcessingValidationError(
            "ProcessingScanResult.run_histories must be a tuple."
        )
    if not isinstance(value.decisions, tuple):
        raise ProcessingValidationError(
            "ProcessingScanResult.decisions must be a tuple."
        )
    if not isinstance(value.issues, tuple):
        raise ProcessingValidationError(
            "ProcessingScanResult.issues must be a tuple."
        )

    for issue in value.issues:
        if not isinstance(issue, ProcessingIssue):
            raise ProcessingValidationError(
                "ProcessingScanResult contains an invalid ProcessingIssue."
            )
        if issue.project_id != expected_project_id:
            raise ProcessingReferenceError(
                "ProcessingIssue project_id does not match the project."
            )

    return value


def _source_index(
    sources: tuple[SourceManifest, ...],
) -> dict[str, SourceManifest]:
    result = {}
    for source in sources:
        if source.source_id in result:
            raise ProcessingIntegrityError(
                f"Duplicate registered source identity: {source.source_id}."
            )
        result[source.source_id] = source
    return result


def _validate_history_references(
    project_id: str,
    histories: tuple[ProcessingRunHistory, ...],
    source_by_id: dict[str, SourceManifest],
) -> None:
    run_ids: set[str] = set()
    for history in histories:
        manifest = history.manifest
        if manifest.project_id != project_id:
            raise ProcessingReferenceError(
                "Processing Run is not project-local."
            )
        if manifest.processing_run_id in run_ids:
            raise ProcessingIntegrityError(
                "Duplicate Processing Run identity: "
                f"{manifest.processing_run_id}."
            )
        run_ids.add(manifest.processing_run_id)

        source = source_by_id.get(manifest.source_id)
        if source is None:
            raise ProcessingReferenceError(
                "Processing Run references an unregistered source: "
                f"{manifest.source_id}."
            )
        if manifest.source_sha256 != source.sha256:
            raise ProcessingReferenceError(
                "Processing Run source fingerprint does not match the "
                "registered source."
            )


def _validate_decision_references(
    project_id: str,
    decisions: tuple[ProcessingDecision, ...],
    source_by_id: dict[str, SourceManifest],
) -> None:
    decision_ids: set[str] = set()
    for decision in decisions:
        if not isinstance(decision, ProcessingDecision):
            raise ProcessingValidationError(
                "ProcessingScanResult contains an invalid decision."
            )
        if decision.project_id != project_id:
            raise ProcessingReferenceError(
                "Processing Decision is not project-local."
            )
        if decision.processing_decision_id in decision_ids:
            raise ProcessingIntegrityError(
                "Duplicate Processing Decision identity: "
                f"{decision.processing_decision_id}."
            )
        decision_ids.add(decision.processing_decision_id)

        source = source_by_id.get(decision.source_id)
        if source is None:
            raise ProcessingReferenceError(
                "Processing Decision references an unregistered source: "
                f"{decision.source_id}."
            )
        if decision.source_sha256 != source.sha256:
            raise ProcessingReferenceError(
                "Processing Decision source fingerprint does not match the "
                "registered source."
            )


def _source_issue_to_processing_issue(
    issue: SourceIssue,
) -> ProcessingIssue:
    return ProcessingIssue(
        project_id=issue.project_id,
        code=issue.code,
        message=issue.message,
        issue_level="blocking",
        path=issue.path,
        source_id=issue.source_id,
    )


def _state_issues(
    project_id: str,
    states: tuple[DerivedProcessingRunState, ...],
    histories: tuple[ProcessingRunHistory, ...],
) -> tuple[ProcessingIssue, ...]:
    source_by_run = {
        history.manifest.processing_run_id: history.manifest.source_id
        for history in histories
    }
    issues = []
    for state in states:
        if state.run_state == "blocked" and state.blocked_reason:
            issues.append(
                ProcessingIssue(
                    project_id=project_id,
                    code=state.blocked_reason,
                    message=(
                        "Current Processing Run is blocked: "
                        f"{state.blocked_reason}."
                    ),
                    issue_level="blocking",
                    source_id=source_by_run.get(state.processing_run_id),
                    processing_run_id=state.processing_run_id,
                    event_id=state.latest_event_id,
                )
            )
        if state.run_state == "failed" and state.failure_reason:
            issues.append(
                ProcessingIssue(
                    project_id=project_id,
                    code=state.failure_reason,
                    message=(
                        "Current Processing Run failed: "
                        f"{state.failure_reason}."
                    ),
                    issue_level="blocking",
                    source_id=source_by_run.get(state.processing_run_id),
                    processing_run_id=state.processing_run_id,
                    event_id=state.latest_event_id,
                )
            )
    return tuple(issues)


def _multiple_current_run_issues(
    project_id: str,
    source_by_id: dict[str, SourceManifest],
    states: tuple[DerivedProcessingRunState, ...],
) -> tuple[ProcessingIssue, ...]:
    issues = []
    for source_id in sorted(source_by_id):
        candidates = tuple(
            state
            for state in states
            if state.source_id == source_id
            and state.run_state != "superseded"
            and state.superseded_by_run_id is None
        )
        if len(candidates) > 1:
            issues.append(
                ProcessingIssue(
                    project_id=project_id,
                    code="multiple_current_processing_runs",
                    message=(
                        "A source has multiple non-superseded Processing "
                        "Runs: "
                        + ", ".join(
                            state.processing_run_id
                            for state in candidates
                        )
                        + "."
                    ),
                    issue_level="blocking",
                    source_id=source_id,
                )
            )
    return tuple(issues)


def _disposition_issues(
    project_id: str,
    sources: tuple[SourceManifest, ...],
    histories: tuple[ProcessingRunHistory, ...],
    decisions: tuple[ProcessingDecision, ...],
    states: tuple[DerivedProcessingRunState, ...],
    impacts: tuple[SourceDispositionImpact, ...],
) -> tuple[ProcessingIssue, ...]:
    try:
        effective = derive_effective_source_dispositions(decisions)
    except ProjectProcessingError:
        effective = {}

    history_by_run = {
        history.manifest.processing_run_id: history
        for history in histories
    }
    states_by_source: dict[str, list[DerivedProcessingRunState]] = {}
    for state in states:
        states_by_source.setdefault(state.source_id, []).append(state)

    issues = []
    impact_by_source = {impact.source_id: impact for impact in impacts}

    for source in sources:
        disposition = _effective_disposition(
            source,
            effective.get(source.source_id),
        )
        candidates = tuple(
            state
            for state in states_by_source.get(source.source_id, ())
            if state.run_state != "superseded"
            and state.superseded_by_run_id is None
        )
        current = candidates[0] if len(candidates) == 1 else None

        if current is not None and disposition != "out_of_scope":
            expected_profile = (
                "engineering_source_processing"
                if disposition == "in_scope"
                else "context_only_processing"
            )
            current_history = history_by_run[current.processing_run_id]
            if current_history.manifest.workflow_profile != expected_profile:
                issues.append(
                    ProcessingIssue(
                        project_id=project_id,
                        code="processing_disposition_run_mismatch",
                        message=(
                            "The current Processing Run workflow profile "
                            "does not match the effective source disposition."
                        ),
                        issue_level="blocking",
                        source_id=source.source_id,
                        processing_run_id=current.processing_run_id,
                    )
                )

        impact = impact_by_source.get(source.source_id)
        if impact is not None and impact.artifact_references:
            issues.append(
                ProcessingIssue(
                    project_id=project_id,
                    code="source_disposition_invalidation_required",
                    message=(
                        "The effective source disposition requires explicit "
                        "artifact invalidation."
                    ),
                    issue_level="blocking",
                    source_id=source.source_id,
                    processing_decision_id=(
                        impact.processing_decision_id
                    ),
                )
            )

    return tuple(issues)


def _artifact_source_issues(
    project_id: str,
    histories: tuple[ProcessingRunHistory, ...],
) -> tuple[ProcessingIssue, ...]:
    source_by_artifact: dict[tuple[str, str], str] = {}
    issues = []
    for history in histories:
        source_id = history.manifest.source_id
        for event in history.events:
            for reference in event.artifact_references:
                key = (
                    reference.artifact_type,
                    reference.artifact_id,
                )
                existing = source_by_artifact.get(key)
                if existing is None:
                    source_by_artifact[key] = source_id
                elif existing != source_id:
                    issues.append(
                        ProcessingIssue(
                            project_id=project_id,
                            code="artifact_cross_source_reference",
                            message=(
                                "One artifact identity is referenced by "
                                "Processing Runs for multiple sources."
                            ),
                            issue_level="blocking",
                            source_id=source_id,
                            processing_run_id=(
                                history.manifest.processing_run_id
                            ),
                            event_id=event.event_id,
                        )
                    )
    return tuple(issues)


def _invalidated_artifact_counts(
    histories: tuple[ProcessingRunHistory, ...],
    lifecycles: tuple[ProcessingArtifactLifecycle, ...],
) -> dict[str, int]:
    source_by_artifact: dict[tuple[str, str], str] = {}
    for history in histories:
        for event in history.events:
            for reference in event.artifact_references:
                key = (
                    reference.artifact_type,
                    reference.artifact_id,
                )
                source_by_artifact.setdefault(
                    key,
                    history.manifest.source_id,
                )

    counts: dict[str, int] = {}
    for lifecycle in lifecycles:
        if lifecycle.lifecycle_state != "invalidated":
            continue
        reference = lifecycle.artifact_reference
        source_id = source_by_artifact.get(
            (reference.artifact_type, reference.artifact_id)
        )
        if source_id is not None:
            counts[source_id] = counts.get(source_id, 0) + 1
    return counts


def _issues_by_source(
    issues: tuple[ProcessingIssue, ...],
    history_by_run_id: dict[str, ProcessingRunHistory],
) -> dict[str, tuple[ProcessingIssue, ...]]:
    grouped: dict[str, list[ProcessingIssue]] = {}
    for issue in issues:
        source_id = issue.source_id
        if source_id is None and issue.processing_run_id is not None:
            history = history_by_run_id.get(issue.processing_run_id)
            if history is not None:
                source_id = history.manifest.source_id
        if source_id is not None:
            grouped.setdefault(source_id, []).append(issue)
    return {
        source_id: tuple(values)
        for source_id, values in grouped.items()
    }


def _derived_issue(
    project_id: str,
    *,
    code: str,
    message: str,
) -> ProcessingIssue:
    return ProcessingIssue(
        project_id=project_id,
        code=code,
        message=message,
        issue_level="blocking",
    )


def _deduplicate_and_sort_issues(
    issues: list[ProcessingIssue],
) -> tuple[ProcessingIssue, ...]:
    unique: dict[tuple[object, ...], ProcessingIssue] = {}
    for issue in issues:
        key = (
            issue.project_id,
            issue.code,
            issue.message,
            issue.issue_level,
            str(issue.path or ""),
            issue.source_id,
            issue.processing_run_id,
            issue.event_id,
            issue.processing_decision_id,
        )
        unique[key] = issue

    return tuple(
        unique[key]
        for key in sorted(
            unique,
            key=lambda item: tuple(
                "" if value is None else str(value)
                for value in item
            ),
        )
    )