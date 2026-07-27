"""UI-independent status and display-model presentation for P7."""

from __future__ import annotations

import re
from typing import Iterable

from modules.project_dashboard.errors import (
    DashboardPresentationError,
    DashboardValidationError,
)
from modules.project_dashboard.references import (
    build_evidence_navigation,
    validate_evidence_navigation,
)
from modules.project_dashboard.types import (
    DASHBOARD_DOCUMENT_RENDER_MODES,
    DASHBOARD_FINGERPRINT_STATUSES,
    DASHBOARD_ISSUE_LEVELS,
    DASHBOARD_STATUS_SEMANTICS,
    DASHBOARD_TRACEABILITY_NODE_TYPES,
    DashboardAttentionReviewView,
    DashboardCoverageView,
    DashboardDocumentPreview,
    DashboardFrameworkLevelCoverage,
    DashboardFrameworkNodeCoverage,
    DashboardHumanReviewRow,
    DashboardIssueView,
    DashboardPotentialSupport,
    DashboardProjectOption,
    DashboardProjectSelection,
    DashboardSectionView,
    DashboardSourceProcessingRow,
    DashboardSourceProcessingView,
    ProjectOverviewView,
    DashboardStatus,
    DashboardTraceabilityEdge,
    DashboardTraceabilityNode,
    DashboardTraceabilityView,
    DashboardValue,
    EvidenceNavigation,
    EvidenceReference,
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
_ISSUE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_.]{0,191}$")

_STATUS_PRESENTATIONS: dict[
    str,
    tuple[str, str, str, str | None],
] = {
    "uncovered": (
        "Uncovered",
        "unavailable",
        "—",
        "No eligible preliminary coverage evidence is available.",
    ),
    "candidate_covered": (
        "Candidate covered",
        "candidate",
        "◐",
        "Eligible unreviewed candidate evidence is available.",
    ),
    "reviewed_candidate_covered": (
        "Reviewed candidate covered",
        "reviewed",
        "✓",
        "Eligible candidate evidence has an exact confirmation.",
    ),
    "partially_covered": (
        "Partially covered",
        "attention",
        "!",
        "Some, but not all, required framework nodes are covered.",
    ),
    "covered": (
        "Covered",
        "reviewed",
        "✓",
        "All required framework nodes have preliminary coverage.",
    ),
    "attention_required": (
        "Attention required",
        "attention",
        "!",
        "The displayed result requires review or contains an issue.",
    ),
    "not_supported": (
        "Not supported",
        "unavailable",
        "—",
        "The required preliminary support evidence is not available.",
    ),
    "partially_supported": (
        "Partially supported",
        "attention",
        "!",
        "Some, but not all, required preliminary support exists.",
    ),
    "potentially_supported": (
        "Potentially supported",
        "candidate",
        "◐",
        "Preliminary evidence may support this scope; it is not approved.",
    ),
    "not_available": (
        "Not available",
        "unavailable",
        "—",
        "This assessment is not available in the current phase.",
    ),
    "created": (
        "Created",
        "informational",
        "ℹ",
        "The Processing Run exists but has not completed.",
    ),
    "running": (
        "Running",
        "informational",
        "ℹ",
        "The Processing Run is currently active.",
    ),
    "completed": (
        "Completed",
        "reviewed",
        "✓",
        "The Processing Run completed operationally; this is not engineering approval.",
    ),
    "failed": (
        "Failed",
        "blocking",
        "×",
        "The Processing Run failed and requires attention.",
    ),
    "blocked": (
        "Blocked",
        "blocking",
        "×",
        "The Processing Run is blocked and cannot continue without resolution.",
    ),
    "empty": (
        "Empty",
        "neutral",
        "○",
        None,
    ),
    "not_started": (
        "Not started",
        "neutral",
        "○",
        None,
    ),
    "in_progress": (
        "In progress",
        "informational",
        "ℹ",
        None,
    ),
    "awaiting_review": (
        "Awaiting review",
        "attention",
        "!",
        None,
    ),
    "partially_processed": (
        "Partially processed",
        "attention",
        "!",
        None,
    ),
    "processed": (
        "Processed",
        "reviewed",
        "✓",
        None,
    ),
    "in_scope": (
        "In scope",
        "informational",
        "ℹ",
        None,
    ),
    "engineering_source": (
        "Engineering source",
        "informational",
        "ℹ",
        "Registered as eligible engineering evidence, subject to processing state.",
    ),
    "context_only": (
        "Context only",
        "neutral",
        "○",
        None,
    ),
    "out_of_scope": (
        "Out of scope",
        "unavailable",
        "—",
        None,
    ),
    "active": (
        "Active",
        "informational",
        "ℹ",
        None,
    ),
    "invalidated": (
        "Invalidated",
        "blocking",
        "×",
        None,
    ),
    "superseded": (
        "Superseded",
        "neutral",
        "○",
        None,
    ),
    "confirm": (
        "Confirmed",
        "reviewed",
        "✓",
        "Confirmation applies only to the exact reviewed target.",
    ),
    "reject": (
        "Rejected",
        "blocking",
        "×",
        None,
    ),
    "request_changes": (
        "Changes requested",
        "attention",
        "!",
        None,
    ),
    "warning": (
        "Warning",
        "attention",
        "!",
        None,
    ),
    "clear": (
        "No attention",
        "reviewed",
        "✓",
        "No warning or blocking issue is present in the displayed overview.",
    ),
    "assigned": (
        "Assigned",
        "candidate",
        "◐",
        "The candidate proposes one or more framework assignments.",
    ),
    "unassigned": (
        "Unassigned",
        "unavailable",
        "—",
        "The candidate does not assign the Information Unit to a framework node.",
    ),
    "ambiguous": (
        "Ambiguous",
        "attention",
        "!",
        "The candidate contains ambiguous assignment evidence.",
    ),
    "conflict": (
        "Conflict",
        "attention",
        "!",
        "The candidate contains conflicting assignment evidence.",
    ),
    "valid": (
        "Valid",
        "reviewed",
        "✓",
        "The exact reference validation succeeded.",
    ),
    "invalid": (
        "Invalid",
        "blocking",
        "×",
        "The exact reference validation failed.",
    ),
    "not_applicable": (
        "Not applicable",
        "neutral",
        "○",
        None,
    ),
    "blocking": (
        "Blocking",
        "blocking",
        "×",
        None,
    ),
}


def present_status(
    state: str,
    *,
    label: str | None = None,
    explanation: str | None = None,
) -> DashboardStatus:
    """Present one known P5/P6/review state without changing its meaning."""

    if not isinstance(state, str) or state not in _STATUS_PRESENTATIONS:
        raise DashboardPresentationError(
            f"Unsupported dashboard status state: {state!r}."
        )

    default_label, semantic, icon, default_explanation = (
        _STATUS_PRESENTATIONS[state]
    )

    selected_label = (
        default_label
        if label is None
        else _require_trimmed_text(label, "label")
    )
    selected_explanation = (
        default_explanation
        if explanation is None
        else _require_trimmed_text(
            explanation,
            "explanation",
        )
    )

    status = DashboardStatus(
        state=state,
        label=selected_label,
        semantic=semantic,
        icon=icon,
        explanation=selected_explanation,
    )
    return validate_dashboard_status(status)


def present_issue_status(issue_level: str) -> DashboardStatus:
    """Map a canonical issue level to status text, icon and semantics."""

    if issue_level not in DASHBOARD_ISSUE_LEVELS:
        raise DashboardPresentationError(
            f"Unsupported issue level: {issue_level!r}."
        )
    return present_status(issue_level)


def validate_dashboard_status(
    value: object,
) -> DashboardStatus:
    """Validate one complete status presentation contract."""

    if not isinstance(value, DashboardStatus):
        raise DashboardValidationError(
            "value must be a DashboardStatus."
        )
    if value.state not in _STATUS_PRESENTATIONS:
        raise DashboardValidationError(
            "status state is unsupported."
        )
    _require_trimmed_text(value.label, "status.label")
    if value.semantic not in DASHBOARD_STATUS_SEMANTICS:
        raise DashboardValidationError(
            "status semantic is invalid."
        )
    _require_trimmed_text(value.icon, "status.icon")
    if value.explanation is not None:
        _require_trimmed_text(
            value.explanation,
            "status.explanation",
        )

    expected_semantic = _STATUS_PRESENTATIONS[value.state][1]
    expected_icon = _STATUS_PRESENTATIONS[value.state][2]
    if value.semantic != expected_semantic:
        raise DashboardValidationError(
            "status semantic changes the meaning of the domain state."
        )
    if value.icon != expected_icon:
        raise DashboardValidationError(
            "status icon does not match the canonical state."
        )

    return value


def make_dashboard_value(
    *,
    value_id: str,
    label: str,
    primary_text: str,
    secondary_text: str | None = None,
    status: DashboardStatus | None = None,
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardValue:
    """Create one validated, display-ready value."""

    navigation = build_evidence_navigation(
        evidence_references
    )
    value = DashboardValue(
        value_id=_require_identifier(value_id, "value_id"),
        label=_require_trimmed_text(label, "label"),
        primary_text=_require_trimmed_text(
            primary_text,
            "primary_text",
        ),
        secondary_text=(
            None
            if secondary_text is None
            else _require_trimmed_text(
                secondary_text,
                "secondary_text",
            )
        ),
        status=(
            None
            if status is None
            else validate_dashboard_status(status)
        ),
        evidence=navigation,
    )
    return validate_dashboard_value(value)


def validate_dashboard_value(
    value: object,
) -> DashboardValue:
    """Validate one display-ready value."""

    if not isinstance(value, DashboardValue):
        raise DashboardValidationError(
            "value must be a DashboardValue."
        )
    _require_identifier(value.value_id, "value_id")
    _require_trimmed_text(value.label, "label")
    _require_trimmed_text(value.primary_text, "primary_text")
    if value.secondary_text is not None:
        _require_trimmed_text(
            value.secondary_text,
            "secondary_text",
        )
    if value.status is not None:
        validate_dashboard_status(value.status)
    validate_evidence_navigation(value.evidence)
    return value


def make_issue_view(
    *,
    issue_code: str,
    message: str,
    issue_level: str,
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardIssueView:
    """Create one validated warning or blocking issue view."""

    issue = DashboardIssueView(
        issue_code=_require_issue_code(issue_code),
        message=_require_trimmed_text(message, "message"),
        issue_level=issue_level,
        status=present_issue_status(issue_level),
        evidence=build_evidence_navigation(
            evidence_references
        ),
    )
    return validate_issue_view(issue)


def validate_issue_view(
    value: object,
) -> DashboardIssueView:
    """Validate one issue presentation."""

    if not isinstance(value, DashboardIssueView):
        raise DashboardValidationError(
            "value must be a DashboardIssueView."
        )
    _require_issue_code(value.issue_code)
    _require_trimmed_text(value.message, "message")
    if value.issue_level not in DASHBOARD_ISSUE_LEVELS:
        raise DashboardValidationError(
            "issue_level is invalid."
        )
    validate_dashboard_status(value.status)
    if value.status.state != value.issue_level:
        raise DashboardValidationError(
            "issue status must match issue_level."
        )
    validate_evidence_navigation(value.evidence)
    return value


def make_section_view(
    *,
    section_id: str,
    title: str,
    description: str | None = None,
    values: Iterable[DashboardValue] = (),
    issues: Iterable[DashboardIssueView] = (),
) -> DashboardSectionView:
    """Create one deterministic section with unique value and issue identities."""

    value_tuple = tuple(values)
    issue_tuple = tuple(issues)

    for item in value_tuple:
        validate_dashboard_value(item)
    for item in issue_tuple:
        validate_issue_view(item)

    _require_unique(
        (item.value_id for item in value_tuple),
        "value_id",
    )
    _require_unique(
        (item.issue_code for item in issue_tuple),
        "issue_code",
    )

    section = DashboardSectionView(
        section_id=_require_identifier(
            section_id,
            "section_id",
        ),
        title=_require_trimmed_text(title, "title"),
        description=(
            None
            if description is None
            else _require_trimmed_text(
                description,
                "description",
            )
        ),
        values=tuple(
            sorted(
                value_tuple,
                key=lambda item: item.value_id,
            )
        ),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda item: (
                    0
                    if item.issue_level == "blocking"
                    else 1,
                    item.issue_code,
                ),
            )
        ),
    )
    return validate_section_view(section)


def validate_section_view(
    value: object,
) -> DashboardSectionView:
    """Validate one canonical dashboard section."""

    if not isinstance(value, DashboardSectionView):
        raise DashboardValidationError(
            "value must be a DashboardSectionView."
        )
    _require_identifier(value.section_id, "section_id")
    _require_trimmed_text(value.title, "title")
    if value.description is not None:
        _require_trimmed_text(
            value.description,
            "description",
        )
    if not isinstance(value.values, tuple):
        raise DashboardValidationError(
            "section values must be a tuple."
        )
    if not isinstance(value.issues, tuple):
        raise DashboardValidationError(
            "section issues must be a tuple."
        )

    for item in value.values:
        validate_dashboard_value(item)
    for item in value.issues:
        validate_issue_view(item)

    if value.values != tuple(
        sorted(
            value.values,
            key=lambda item: item.value_id,
        )
    ):
        raise DashboardValidationError(
            "section values must be sorted by value_id."
        )
    if value.issues != tuple(
        sorted(
            value.issues,
            key=lambda item: (
                0 if item.issue_level == "blocking" else 1,
                item.issue_code,
            ),
        )
    ):
        raise DashboardValidationError(
            "section issues must be sorted deterministically."
        )

    _require_unique(
        (item.value_id for item in value.values),
        "value_id",
    )
    _require_unique(
        (item.issue_code for item in value.issues),
        "issue_code",
    )
    return value


def status_semantic_for_state(state: str) -> str:
    """Expose the semantic token without exposing decorative color values."""

    return present_status(state).semantic


def supported_dashboard_states() -> tuple[str, ...]:
    """Return the canonical supported domain states."""

    return tuple(sorted(_STATUS_PRESENTATIONS))


def _require_identifier(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or _IDENTIFIER_PATTERN.fullmatch(value) is None
    ):
        raise DashboardValidationError(
            f"{label} must be a lowercase snake-case identifier."
        )
    return value



def _require_issue_code(value: object) -> str:
    if (
        not isinstance(value, str)
        or _ISSUE_CODE_PATTERN.fullmatch(value) is None
    ):
        raise DashboardValidationError(
            "issue_code must be a lowercase dotted identifier."
        )
    return value


def _require_trimmed_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise DashboardValidationError(
            f"{label} must be a trimmed non-empty string."
        )
    return value


def _require_unique(
    values: Iterable[str],
    label: str,
) -> None:
    supplied = tuple(values)
    if len(supplied) != len(set(supplied)):
        raise DashboardValidationError(
            f"{label} values must be unique."
        )


_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")


def make_project_option(
    *,
    project_id: str,
    display_name: str,
    description: str,
    framework_template_id: str,
    framework_template_version: str,
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardProjectOption:
    """Create one deterministic project selector option."""

    validated_project_id = _require_project_id(project_id)
    validated_display_name = _require_trimmed_text(
        display_name,
        "display_name",
    )
    if not isinstance(description, str) or description != description.strip():
        raise DashboardValidationError(
            "description must be a trimmed string."
        )
    option = DashboardProjectOption(
        project_id=validated_project_id,
        display_name=validated_display_name,
        description=description,
        label=f"{validated_display_name} · {validated_project_id}",
        framework_template_id=_require_trimmed_text(
            framework_template_id,
            "framework_template_id",
        ),
        framework_template_version=_require_trimmed_text(
            framework_template_version,
            "framework_template_version",
        ),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_project_option(option)


def validate_project_option(
    value: object,
) -> DashboardProjectOption:
    """Validate one display-ready project option."""

    if not isinstance(value, DashboardProjectOption):
        raise DashboardValidationError(
            "value must be a DashboardProjectOption."
        )
    _require_project_id(value.project_id)
    _require_trimmed_text(value.display_name, "display_name")
    if not isinstance(value.description, str) or value.description != value.description.strip():
        raise DashboardValidationError(
            "description must be a trimmed string."
        )
    expected_label = f"{value.display_name} · {value.project_id}"
    if value.label != expected_label:
        raise DashboardValidationError(
            "project option label must contain display name and project ID."
        )
    _require_trimmed_text(
        value.framework_template_id,
        "framework_template_id",
    )
    _require_trimmed_text(
        value.framework_template_version,
        "framework_template_version",
    )
    validate_evidence_navigation(value.evidence)
    return value


def make_project_selection(
    *,
    projects: Iterable[DashboardProjectOption] = (),
    issues: Iterable[DashboardIssueView] = (),
) -> DashboardProjectSelection:
    """Create the deterministic project selection model."""

    project_tuple = tuple(projects)
    issue_tuple = tuple(issues)
    for project in project_tuple:
        validate_project_option(project)
    for issue in issue_tuple:
        validate_issue_view(issue)
    _require_unique(
        (project.project_id for project in project_tuple),
        "project_id",
    )
    selection = DashboardProjectSelection(
        projects=tuple(
            sorted(
                project_tuple,
                key=lambda project: (
                    project.display_name.casefold(),
                    project.display_name,
                    project.project_id,
                ),
            )
        ),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda issue: (
                    0 if issue.issue_level == "blocking" else 1,
                    issue.issue_code,
                    issue.message,
                ),
            )
        ),
    )
    return validate_project_selection(selection)


def validate_project_selection(
    value: object,
) -> DashboardProjectSelection:
    """Validate the complete project selector model."""

    if not isinstance(value, DashboardProjectSelection):
        raise DashboardValidationError(
            "value must be a DashboardProjectSelection."
        )
    if not isinstance(value.projects, tuple):
        raise DashboardValidationError(
            "projects must be a tuple."
        )
    if not isinstance(value.issues, tuple):
        raise DashboardValidationError(
            "issues must be a tuple."
        )
    for project in value.projects:
        validate_project_option(project)
    for issue in value.issues:
        validate_issue_view(issue)
    expected_projects = tuple(
        sorted(
            value.projects,
            key=lambda project: (
                project.display_name.casefold(),
                project.display_name,
                project.project_id,
            ),
        )
    )
    if value.projects != expected_projects:
        raise DashboardValidationError(
            "projects must be sorted by display name and project ID."
        )
    expected_issues = tuple(
        sorted(
            value.issues,
            key=lambda issue: (
                0 if issue.issue_level == "blocking" else 1,
                issue.issue_code,
                issue.message,
            ),
        )
    )
    if value.issues != expected_issues:
        raise DashboardValidationError(
            "project selection issues must be sorted deterministically."
        )
    _require_unique(
        (project.project_id for project in value.projects),
        "project_id",
    )
    return value


def make_project_overview(
    *,
    project: DashboardProjectOption,
    section: DashboardSectionView,
) -> ProjectOverviewView:
    """Bind one selected project to the canonical overview section."""

    validated_project = validate_project_option(project)
    validated_section = validate_section_view(section)
    if validated_section.section_id != "project_overview":
        raise DashboardValidationError(
            "Project Overview section_id must be project_overview."
        )
    overview = ProjectOverviewView(
        project=validated_project,
        section=validated_section,
    )
    return validate_project_overview(overview)


def validate_project_overview(
    value: object,
) -> ProjectOverviewView:
    """Validate one complete Project Overview view model."""

    if not isinstance(value, ProjectOverviewView):
        raise DashboardValidationError(
            "value must be a ProjectOverviewView."
        )
    validate_project_option(value.project)
    validate_section_view(value.section)
    if value.section.section_id != "project_overview":
        raise DashboardValidationError(
            "Project Overview section_id must be project_overview."
        )
    return value


def _require_project_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _PROJECT_ID_PATTERN.fullmatch(value) is None
    ):
        raise DashboardValidationError(
            "project_id must be a six-digit numeric string."
        )
    return value


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def make_source_processing_row(
    *,
    project_id: str,
    source_id: str,
    original_filename: str,
    source_role: str,
    media_type: str,
    size_bytes: int,
    sha256: str,
    processing_disposition: str,
    current_processing_run_id: str | None,
    run_state: str | None,
    processing_stage: str | None,
    latest_attempt_id: str | None,
    pending_review: bool,
    superseded_run_ids: Iterable[str] = (),
    invalidated_artifact_count: int = 0,
    blocking_issue_codes: Iterable[str] = (),
    failure_issue_codes: Iterable[str] = (),
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardSourceProcessingRow:
    """Create one display-ready Source and Processing row."""

    selected_run_state = "not_started" if run_state is None else run_state
    row = DashboardSourceProcessingRow(
        project_id=_require_project_id(project_id),
        source_id=_require_trimmed_text(source_id, "source_id"),
        original_filename=_require_trimmed_text(
            original_filename,
            "original_filename",
        ),
        source_role=_require_trimmed_text(source_role, "source_role"),
        media_type=_require_trimmed_text(media_type, "media_type"),
        size_bytes=_require_positive_int(size_bytes, "size_bytes"),
        sha256=_require_sha256(sha256),
        processing_disposition=_require_trimmed_text(
            processing_disposition,
            "processing_disposition",
        ),
        current_processing_run_id=_optional_trimmed_text(
            current_processing_run_id,
            "current_processing_run_id",
        ),
        run_state=(
            None
            if run_state is None
            else _require_trimmed_text(run_state, "run_state")
        ),
        processing_stage=_optional_trimmed_text(
            processing_stage,
            "processing_stage",
        ),
        latest_attempt_id=_optional_trimmed_text(
            latest_attempt_id,
            "latest_attempt_id",
        ),
        pending_review=_require_bool(pending_review, "pending_review"),
        superseded_run_ids=_canonical_text_tuple(
            superseded_run_ids,
            "superseded_run_ids",
        ),
        invalidated_artifact_count=_require_non_negative_int(
            invalidated_artifact_count,
            "invalidated_artifact_count",
        ),
        blocking_issue_codes=_canonical_text_tuple(
            blocking_issue_codes,
            "blocking_issue_codes",
        ),
        failure_issue_codes=_canonical_text_tuple(
            failure_issue_codes,
            "failure_issue_codes",
        ),
        disposition_status=present_status(processing_disposition),
        run_status=present_status(selected_run_state),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_source_processing_row(row)


def validate_source_processing_row(
    value: object,
) -> DashboardSourceProcessingRow:
    """Validate one Source and Processing row."""

    if not isinstance(value, DashboardSourceProcessingRow):
        raise DashboardValidationError(
            "value must be a DashboardSourceProcessingRow."
        )
    _require_project_id(value.project_id)
    _require_trimmed_text(value.source_id, "source_id")
    _require_trimmed_text(value.original_filename, "original_filename")
    _require_trimmed_text(value.source_role, "source_role")
    _require_trimmed_text(value.media_type, "media_type")
    _require_positive_int(value.size_bytes, "size_bytes")
    _require_sha256(value.sha256)
    _require_trimmed_text(
        value.processing_disposition,
        "processing_disposition",
    )
    _optional_trimmed_text(
        value.current_processing_run_id,
        "current_processing_run_id",
    )
    _optional_trimmed_text(value.run_state, "run_state")
    _optional_trimmed_text(value.processing_stage, "processing_stage")
    _optional_trimmed_text(value.latest_attempt_id, "latest_attempt_id")
    _require_bool(value.pending_review, "pending_review")
    _require_canonical_text_tuple(
        value.superseded_run_ids,
        "superseded_run_ids",
    )
    _require_non_negative_int(
        value.invalidated_artifact_count,
        "invalidated_artifact_count",
    )
    _require_canonical_text_tuple(
        value.blocking_issue_codes,
        "blocking_issue_codes",
    )
    _require_canonical_text_tuple(
        value.failure_issue_codes,
        "failure_issue_codes",
    )
    validate_dashboard_status(value.disposition_status)
    validate_dashboard_status(value.run_status)
    if value.disposition_status.state != value.processing_disposition:
        raise DashboardValidationError(
            "disposition status must preserve the P5 disposition."
        )
    expected_run_state = "not_started" if value.run_state is None else value.run_state
    if value.run_status.state != expected_run_state:
        raise DashboardValidationError(
            "run status must preserve the P5 run state."
        )
    if value.current_processing_run_id is None and value.run_state is not None:
        raise DashboardValidationError(
            "run_state requires current_processing_run_id."
        )
    if value.current_processing_run_id is not None and value.run_state is None:
        raise DashboardValidationError(
            "current_processing_run_id requires run_state."
        )
    validate_evidence_navigation(value.evidence)
    return value


def make_source_processing_view(
    *,
    project_id: str,
    project_state: str,
    sources: Iterable[DashboardSourceProcessingRow],
    issues: Iterable[DashboardIssueView] = (),
) -> DashboardSourceProcessingView:
    """Create one deterministic detailed Sources and Processing view."""

    source_tuple = tuple(sources)
    issue_tuple = tuple(issues)
    for row in source_tuple:
        validate_source_processing_row(row)
    for issue in issue_tuple:
        validate_issue_view(issue)
    _require_unique((row.source_id for row in source_tuple), "source_id")
    _require_unique((issue.issue_code for issue in issue_tuple), "issue_code")
    view = DashboardSourceProcessingView(
        project_id=_require_project_id(project_id),
        project_state=_require_trimmed_text(project_state, "project_state"),
        project_status=present_status(project_state),
        sources=tuple(sorted(source_tuple, key=lambda row: row.source_id)),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda item: (
                    0 if item.issue_level == "blocking" else 1,
                    item.issue_code,
                ),
            )
        ),
    )
    return validate_source_processing_view(view)


def validate_source_processing_view(
    value: object,
) -> DashboardSourceProcessingView:
    """Validate one detailed Sources and Processing view."""

    if not isinstance(value, DashboardSourceProcessingView):
        raise DashboardValidationError(
            "value must be a DashboardSourceProcessingView."
        )
    _require_project_id(value.project_id)
    _require_trimmed_text(value.project_state, "project_state")
    validate_dashboard_status(value.project_status)
    if value.project_status.state != value.project_state:
        raise DashboardValidationError(
            "project status must preserve the P5 project state."
        )
    if not isinstance(value.sources, tuple) or not isinstance(value.issues, tuple):
        raise DashboardValidationError(
            "sources and issues must be tuples."
        )
    for row in value.sources:
        validate_source_processing_row(row)
        if row.project_id != value.project_id:
            raise DashboardValidationError(
                "source row belongs to another project."
            )
    for issue in value.issues:
        validate_issue_view(issue)
    if value.sources != tuple(sorted(value.sources, key=lambda row: row.source_id)):
        raise DashboardValidationError(
            "source rows must be sorted by source_id."
        )
    _require_unique((row.source_id for row in value.sources), "source_id")
    _require_unique((issue.issue_code for issue in value.issues), "issue_code")
    return value


def make_framework_level_coverage_view(
    *,
    display_order: int,
    level_node_id: str,
    level_name: str,
    coverage_state: str,
    covered_node_count: int,
    total_node_count: int,
    candidate_covered_node_count: int,
    reviewed_candidate_covered_node_count: int,
    attention_node_count: int,
    covered_node_ids: Iterable[str] = (),
    uncovered_node_ids: Iterable[str] = (),
    attention_node_ids: Iterable[str] = (),
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardFrameworkLevelCoverage:
    """Create one display-ready framework-level coverage row."""

    row = DashboardFrameworkLevelCoverage(
        display_order=_require_positive_int(display_order, "display_order"),
        level_node_id=_require_trimmed_text(level_node_id, "level_node_id"),
        level_name=_require_trimmed_text(level_name, "level_name"),
        coverage_state=_require_trimmed_text(coverage_state, "coverage_state"),
        covered_node_count=_require_non_negative_int(
            covered_node_count,
            "covered_node_count",
        ),
        total_node_count=_require_positive_int(total_node_count, "total_node_count"),
        candidate_covered_node_count=_require_non_negative_int(
            candidate_covered_node_count,
            "candidate_covered_node_count",
        ),
        reviewed_candidate_covered_node_count=_require_non_negative_int(
            reviewed_candidate_covered_node_count,
            "reviewed_candidate_covered_node_count",
        ),
        attention_node_count=_require_non_negative_int(
            attention_node_count,
            "attention_node_count",
        ),
        covered_node_ids=_canonical_text_tuple(covered_node_ids, "covered_node_ids"),
        uncovered_node_ids=_canonical_text_tuple(
            uncovered_node_ids,
            "uncovered_node_ids",
        ),
        attention_node_ids=_canonical_text_tuple(
            attention_node_ids,
            "attention_node_ids",
        ),
        status=present_status(coverage_state),
        attention_status=(
            present_status("attention_required")
            if attention_node_count > 0
            else None
        ),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_framework_level_coverage_view(row)


def validate_framework_level_coverage_view(
    value: object,
) -> DashboardFrameworkLevelCoverage:
    """Validate one framework-level coverage row."""

    if not isinstance(value, DashboardFrameworkLevelCoverage):
        raise DashboardValidationError(
            "value must be a DashboardFrameworkLevelCoverage."
        )
    _require_positive_int(value.display_order, "display_order")
    _require_trimmed_text(value.level_node_id, "level_node_id")
    _require_trimmed_text(value.level_name, "level_name")
    _require_trimmed_text(value.coverage_state, "coverage_state")
    total = _require_positive_int(value.total_node_count, "total_node_count")
    for label, count in (
        ("covered_node_count", value.covered_node_count),
        ("candidate_covered_node_count", value.candidate_covered_node_count),
        ("reviewed_candidate_covered_node_count", value.reviewed_candidate_covered_node_count),
        ("attention_node_count", value.attention_node_count),
    ):
        _require_non_negative_int(count, label)
        if count > total:
            raise DashboardValidationError(f"{label} cannot exceed total_node_count.")
    if (
        value.candidate_covered_node_count
        + value.reviewed_candidate_covered_node_count
        != value.covered_node_count
    ):
        raise DashboardValidationError(
            "candidate and reviewed counts must equal covered_node_count."
        )
    for label, values in (
        ("covered_node_ids", value.covered_node_ids),
        ("uncovered_node_ids", value.uncovered_node_ids),
        ("attention_node_ids", value.attention_node_ids),
    ):
        _require_canonical_text_tuple(values, label)
    if len(value.covered_node_ids) != value.covered_node_count:
        raise DashboardValidationError(
            "covered_node_ids must match covered_node_count."
        )
    if len(value.covered_node_ids) + len(value.uncovered_node_ids) != total:
        raise DashboardValidationError(
            "covered and uncovered node IDs must match total_node_count."
        )
    if len(value.attention_node_ids) != value.attention_node_count:
        raise DashboardValidationError(
            "attention_node_ids must match attention_node_count."
        )
    validate_dashboard_status(value.status)
    if value.status.state != value.coverage_state:
        raise DashboardValidationError(
            "level status must preserve coverage_state."
        )
    if (value.attention_status is None) != (value.attention_node_count == 0):
        raise DashboardValidationError(
            "attention status must match attention_node_count."
        )
    if value.attention_status is not None:
        validate_dashboard_status(value.attention_status)
        if value.attention_status.state != "attention_required":
            raise DashboardValidationError(
                "attention status must be attention_required."
            )
    validate_evidence_navigation(value.evidence)
    return value


def make_framework_node_coverage_view(
    *,
    display_order: int,
    framework_node_id: str,
    mapping_key: str,
    node_name: str,
    level_node_id: str,
    coverage_state: str,
    attention_required: bool,
    eligible_source_count: int,
    information_unit_count: int,
    assignment_candidate_count: int,
    confirmed_candidate_count: int,
    unreviewed_candidate_count: int,
    rejected_candidate_count: int,
    ambiguous_candidate_count: int,
    conflicting_candidate_count: int,
    source_ids: Iterable[str] = (),
    information_unit_ids: Iterable[str] = (),
    framework_assignment_candidate_ids: Iterable[str] = (),
    human_review_decision_ids: Iterable[str] = (),
    issue_codes: Iterable[str] = (),
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardFrameworkNodeCoverage:
    """Create one display-ready framework-node coverage row."""

    row = DashboardFrameworkNodeCoverage(
        display_order=_require_positive_int(display_order, "display_order"),
        framework_node_id=_require_trimmed_text(
            framework_node_id,
            "framework_node_id",
        ),
        mapping_key=_require_trimmed_text(mapping_key, "mapping_key"),
        node_name=_require_trimmed_text(node_name, "node_name"),
        level_node_id=_require_trimmed_text(level_node_id, "level_node_id"),
        coverage_state=_require_trimmed_text(coverage_state, "coverage_state"),
        attention_required=_require_bool(attention_required, "attention_required"),
        eligible_source_count=_require_non_negative_int(
            eligible_source_count,
            "eligible_source_count",
        ),
        information_unit_count=_require_non_negative_int(
            information_unit_count,
            "information_unit_count",
        ),
        assignment_candidate_count=_require_non_negative_int(
            assignment_candidate_count,
            "assignment_candidate_count",
        ),
        confirmed_candidate_count=_require_non_negative_int(
            confirmed_candidate_count,
            "confirmed_candidate_count",
        ),
        unreviewed_candidate_count=_require_non_negative_int(
            unreviewed_candidate_count,
            "unreviewed_candidate_count",
        ),
        rejected_candidate_count=_require_non_negative_int(
            rejected_candidate_count,
            "rejected_candidate_count",
        ),
        ambiguous_candidate_count=_require_non_negative_int(
            ambiguous_candidate_count,
            "ambiguous_candidate_count",
        ),
        conflicting_candidate_count=_require_non_negative_int(
            conflicting_candidate_count,
            "conflicting_candidate_count",
        ),
        source_ids=_canonical_text_tuple(source_ids, "source_ids"),
        information_unit_ids=_canonical_text_tuple(
            information_unit_ids,
            "information_unit_ids",
        ),
        framework_assignment_candidate_ids=_canonical_text_tuple(
            framework_assignment_candidate_ids,
            "framework_assignment_candidate_ids",
        ),
        human_review_decision_ids=_canonical_text_tuple(
            human_review_decision_ids,
            "human_review_decision_ids",
        ),
        issue_codes=_canonical_text_tuple(issue_codes, "issue_codes"),
        status=present_status(coverage_state),
        attention_status=(
            present_status("attention_required")
            if attention_required
            else None
        ),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_framework_node_coverage_view(row)


def validate_framework_node_coverage_view(
    value: object,
) -> DashboardFrameworkNodeCoverage:
    """Validate one framework-node coverage row."""

    if not isinstance(value, DashboardFrameworkNodeCoverage):
        raise DashboardValidationError(
            "value must be a DashboardFrameworkNodeCoverage."
        )
    _require_positive_int(value.display_order, "display_order")
    for label, text in (
        ("framework_node_id", value.framework_node_id),
        ("mapping_key", value.mapping_key),
        ("node_name", value.node_name),
        ("level_node_id", value.level_node_id),
        ("coverage_state", value.coverage_state),
    ):
        _require_trimmed_text(text, label)
    _require_bool(value.attention_required, "attention_required")
    for label, count in (
        ("eligible_source_count", value.eligible_source_count),
        ("information_unit_count", value.information_unit_count),
        ("assignment_candidate_count", value.assignment_candidate_count),
        ("confirmed_candidate_count", value.confirmed_candidate_count),
        ("unreviewed_candidate_count", value.unreviewed_candidate_count),
        ("rejected_candidate_count", value.rejected_candidate_count),
        ("ambiguous_candidate_count", value.ambiguous_candidate_count),
        ("conflicting_candidate_count", value.conflicting_candidate_count),
    ):
        _require_non_negative_int(count, label)
    for label, values in (
        ("source_ids", value.source_ids),
        ("information_unit_ids", value.information_unit_ids),
        ("framework_assignment_candidate_ids", value.framework_assignment_candidate_ids),
        ("human_review_decision_ids", value.human_review_decision_ids),
        ("issue_codes", value.issue_codes),
    ):
        _require_canonical_text_tuple(values, label)
    if len(value.source_ids) != value.eligible_source_count:
        raise DashboardValidationError(
            "source_ids must match eligible_source_count."
        )
    if len(value.information_unit_ids) != value.information_unit_count:
        raise DashboardValidationError(
            "information_unit_ids must match information_unit_count."
        )
    if value.assignment_candidate_count > len(
        value.framework_assignment_candidate_ids
    ):
        raise DashboardValidationError(
            "covering candidate count cannot exceed auditable candidate IDs."
        )
    if (
        value.confirmed_candidate_count
        + value.unreviewed_candidate_count
        != value.assignment_candidate_count
    ):
        raise DashboardValidationError(
            "confirmed and unreviewed counts must equal covering candidate count."
        )
    validate_dashboard_status(value.status)
    if value.status.state != value.coverage_state:
        raise DashboardValidationError(
            "node status must preserve coverage_state."
        )
    if (value.attention_status is None) == value.attention_required:
        raise DashboardValidationError(
            "attention status must match attention_required."
        )
    if value.attention_status is not None:
        validate_dashboard_status(value.attention_status)
        if value.attention_status.state != "attention_required":
            raise DashboardValidationError(
                "attention status must be attention_required."
            )
    validate_evidence_navigation(value.evidence)
    return value


def make_potential_support_view(
    *,
    display_order: int,
    support_target_id: str,
    name: str,
    support_target_type: str,
    support_state: str,
    required_framework_node_ids: Iterable[str] = (),
    covered_framework_node_ids: Iterable[str] = (),
    missing_framework_node_ids: Iterable[str] = (),
    required_support_target_ids: Iterable[str] = (),
    satisfied_support_target_ids: Iterable[str] = (),
    unsatisfied_support_target_ids: Iterable[str] = (),
    attention_required: bool,
    issue_codes: Iterable[str] = (),
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardPotentialSupport:
    """Create one display-ready potential model-support row."""

    row = DashboardPotentialSupport(
        display_order=_require_positive_int(display_order, "display_order"),
        support_target_id=_require_trimmed_text(
            support_target_id,
            "support_target_id",
        ),
        name=_require_trimmed_text(name, "name"),
        support_target_type=_require_trimmed_text(
            support_target_type,
            "support_target_type",
        ),
        support_state=_require_trimmed_text(support_state, "support_state"),
        required_framework_node_ids=_canonical_text_tuple(
            required_framework_node_ids,
            "required_framework_node_ids",
        ),
        covered_framework_node_ids=_canonical_text_tuple(
            covered_framework_node_ids,
            "covered_framework_node_ids",
        ),
        missing_framework_node_ids=_canonical_text_tuple(
            missing_framework_node_ids,
            "missing_framework_node_ids",
        ),
        required_support_target_ids=_canonical_text_tuple(
            required_support_target_ids,
            "required_support_target_ids",
        ),
        satisfied_support_target_ids=_canonical_text_tuple(
            satisfied_support_target_ids,
            "satisfied_support_target_ids",
        ),
        unsatisfied_support_target_ids=_canonical_text_tuple(
            unsatisfied_support_target_ids,
            "unsatisfied_support_target_ids",
        ),
        attention_required=_require_bool(attention_required, "attention_required"),
        issue_codes=_canonical_text_tuple(issue_codes, "issue_codes"),
        status=present_status(support_state),
        attention_status=(
            present_status("attention_required")
            if attention_required
            else None
        ),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_potential_support_view(row)


def validate_potential_support_view(
    value: object,
) -> DashboardPotentialSupport:
    """Validate one potential model-support row."""

    if not isinstance(value, DashboardPotentialSupport):
        raise DashboardValidationError(
            "value must be a DashboardPotentialSupport."
        )
    _require_positive_int(value.display_order, "display_order")
    for label, text in (
        ("support_target_id", value.support_target_id),
        ("name", value.name),
        ("support_target_type", value.support_target_type),
        ("support_state", value.support_state),
    ):
        _require_trimmed_text(text, label)
    for label, values in (
        ("required_framework_node_ids", value.required_framework_node_ids),
        ("covered_framework_node_ids", value.covered_framework_node_ids),
        ("missing_framework_node_ids", value.missing_framework_node_ids),
        ("required_support_target_ids", value.required_support_target_ids),
        ("satisfied_support_target_ids", value.satisfied_support_target_ids),
        ("unsatisfied_support_target_ids", value.unsatisfied_support_target_ids),
        ("issue_codes", value.issue_codes),
    ):
        _require_canonical_text_tuple(values, label)
    if set(value.covered_framework_node_ids) | set(value.missing_framework_node_ids) != set(
        value.required_framework_node_ids
    ):
        raise DashboardValidationError(
            "covered and missing framework nodes must partition required nodes."
        )
    if set(value.satisfied_support_target_ids) | set(
        value.unsatisfied_support_target_ids
    ) != set(value.required_support_target_ids):
        raise DashboardValidationError(
            "satisfied and unsatisfied dependencies must partition required dependencies."
        )
    _require_bool(value.attention_required, "attention_required")
    validate_dashboard_status(value.status)
    if value.status.state != value.support_state:
        raise DashboardValidationError(
            "support status must preserve support_state."
        )
    if (value.attention_status is None) == value.attention_required:
        raise DashboardValidationError(
            "attention status must match attention_required."
        )
    if value.attention_status is not None:
        validate_dashboard_status(value.attention_status)
    validate_evidence_navigation(value.evidence)
    return value


def make_coverage_view(
    *,
    project_id: str,
    project_coverage_state: str,
    framework_template_id: str,
    framework_template_version: str,
    support_profile_id: str,
    support_profile_version: str,
    levels: Iterable[DashboardFrameworkLevelCoverage],
    nodes: Iterable[DashboardFrameworkNodeCoverage],
    support_targets: Iterable[DashboardPotentialSupport],
    approved_readiness_status: str,
    approved_readiness_available_from_phase: str,
    issues: Iterable[DashboardIssueView] = (),
) -> DashboardCoverageView:
    """Create one deterministic detailed P6 dashboard view."""

    level_tuple = tuple(levels)
    node_tuple = tuple(nodes)
    support_tuple = tuple(support_targets)
    issue_tuple = tuple(issues)
    for item in level_tuple:
        validate_framework_level_coverage_view(item)
    for item in node_tuple:
        validate_framework_node_coverage_view(item)
    for item in support_tuple:
        validate_potential_support_view(item)
    for issue in issue_tuple:
        validate_issue_view(issue)
    _require_unique((item.level_node_id for item in level_tuple), "level_node_id")
    _require_unique((item.framework_node_id for item in node_tuple), "framework_node_id")
    _require_unique((item.support_target_id for item in support_tuple), "support_target_id")
    _require_unique((item.issue_code for item in issue_tuple), "issue_code")
    view = DashboardCoverageView(
        project_id=_require_project_id(project_id),
        project_coverage_state=_require_trimmed_text(
            project_coverage_state,
            "project_coverage_state",
        ),
        project_status=present_status(project_coverage_state),
        framework_template_id=_require_trimmed_text(
            framework_template_id,
            "framework_template_id",
        ),
        framework_template_version=_require_trimmed_text(
            framework_template_version,
            "framework_template_version",
        ),
        support_profile_id=_require_trimmed_text(
            support_profile_id,
            "support_profile_id",
        ),
        support_profile_version=_require_trimmed_text(
            support_profile_version,
            "support_profile_version",
        ),
        levels=tuple(sorted(level_tuple, key=lambda item: (item.display_order, item.level_node_id))),
        nodes=tuple(sorted(node_tuple, key=lambda item: (item.display_order, item.framework_node_id))),
        support_targets=tuple(
            sorted(
                support_tuple,
                key=lambda item: (item.display_order, item.support_target_id),
            )
        ),
        approved_readiness_status=_require_trimmed_text(
            approved_readiness_status,
            "approved_readiness_status",
        ),
        approved_readiness_available_from_phase=_require_trimmed_text(
            approved_readiness_available_from_phase,
            "approved_readiness_available_from_phase",
        ),
        approved_readiness=present_status(approved_readiness_status),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda item: (
                    0 if item.issue_level == "blocking" else 1,
                    item.issue_code,
                ),
            )
        ),
    )
    return validate_coverage_view(view)


def validate_coverage_view(value: object) -> DashboardCoverageView:
    """Validate one detailed P6 dashboard view."""

    if not isinstance(value, DashboardCoverageView):
        raise DashboardValidationError(
            "value must be a DashboardCoverageView."
        )
    _require_project_id(value.project_id)
    for label, text in (
        ("project_coverage_state", value.project_coverage_state),
        ("framework_template_id", value.framework_template_id),
        ("framework_template_version", value.framework_template_version),
        ("support_profile_id", value.support_profile_id),
        ("support_profile_version", value.support_profile_version),
        ("approved_readiness_status", value.approved_readiness_status),
        ("approved_readiness_available_from_phase", value.approved_readiness_available_from_phase),
    ):
        _require_trimmed_text(text, label)
    validate_dashboard_status(value.project_status)
    if value.project_status.state != value.project_coverage_state:
        raise DashboardValidationError(
            "project coverage status must preserve P6 state."
        )
    validate_dashboard_status(value.approved_readiness)
    if value.approved_readiness.state != value.approved_readiness_status:
        raise DashboardValidationError(
            "approved readiness presentation must preserve P6 status."
        )
    for item in value.levels:
        validate_framework_level_coverage_view(item)
    for item in value.nodes:
        validate_framework_node_coverage_view(item)
    for item in value.support_targets:
        validate_potential_support_view(item)
    for issue in value.issues:
        validate_issue_view(issue)
    if value.levels != tuple(sorted(value.levels, key=lambda item: (item.display_order, item.level_node_id))):
        raise DashboardValidationError("levels must be sorted deterministically.")
    if value.nodes != tuple(sorted(value.nodes, key=lambda item: (item.display_order, item.framework_node_id))):
        raise DashboardValidationError("nodes must be sorted deterministically.")
    if value.support_targets != tuple(sorted(value.support_targets, key=lambda item: (item.display_order, item.support_target_id))):
        raise DashboardValidationError("support targets must be sorted deterministically.")
    _require_unique((item.level_node_id for item in value.levels), "level_node_id")
    _require_unique((item.framework_node_id for item in value.nodes), "framework_node_id")
    _require_unique((item.support_target_id for item in value.support_targets), "support_target_id")
    known_levels = {item.level_node_id for item in value.levels}
    if any(item.level_node_id not in known_levels for item in value.nodes):
        raise DashboardValidationError(
            "every node must reference a displayed framework level."
        )
    return value


def _require_positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise DashboardValidationError(f"{label} must be a positive integer.")
    return value


def _require_non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise DashboardValidationError(
            f"{label} must be a non-negative integer."
        )
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise DashboardValidationError(f"{label} must be bool.")
    return value


def _optional_trimmed_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _require_trimmed_text(value, label)


def _require_sha256(value: object) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise DashboardValidationError(
            "sha256 must contain exactly 64 lowercase hexadecimal characters."
        )
    return value


def _canonical_text_tuple(values: Iterable[str], label: str) -> tuple[str, ...]:
    supplied = tuple(_require_trimmed_text(item, label) for item in values)
    return tuple(sorted(set(supplied)))


def _require_canonical_text_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DashboardValidationError(f"{label} must be a tuple.")
    canonical = _canonical_text_tuple(value, label)
    if value != canonical:
        raise DashboardValidationError(
            f"{label} must be sorted and unique."
        )
    return value



def make_human_review_row(
    *,
    project_id: str,
    human_review_decision_id: str,
    target_type: str,
    target_id: str,
    target_content_fingerprint: str,
    reference_validation_status: str,
    reference_validation_fingerprint: str | None,
    review_mode: str,
    decision: str,
    reviewer_identity: str,
    rationale: str | None,
    decided_at: str,
    decision_fingerprint: str,
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardHumanReviewRow:
    """Create one deterministic Human Review row."""

    row = DashboardHumanReviewRow(
        project_id=_require_project_id(project_id),
        human_review_decision_id=_require_trimmed_text(
            human_review_decision_id,
            "human_review_decision_id",
        ),
        target_type=_require_trimmed_text(target_type, "target_type"),
        target_id=_require_trimmed_text(target_id, "target_id"),
        target_content_fingerprint=_require_sha256(
            target_content_fingerprint
        ),
        reference_validation_status=_require_trimmed_text(
            reference_validation_status,
            "reference_validation_status",
        ),
        reference_validation_fingerprint=(
            None
            if reference_validation_fingerprint is None
            else _require_sha256(reference_validation_fingerprint)
        ),
        review_mode=_require_trimmed_text(review_mode, "review_mode"),
        decision=_require_trimmed_text(decision, "decision"),
        reviewer_identity=_require_trimmed_text(
            reviewer_identity,
            "reviewer_identity",
        ),
        rationale=_optional_trimmed_text(rationale, "rationale"),
        decided_at=_require_trimmed_text(decided_at, "decided_at"),
        decision_fingerprint=_require_sha256(decision_fingerprint),
        status=present_status(decision),
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_human_review_row(row)


def validate_human_review_row(
    value: object,
) -> DashboardHumanReviewRow:
    """Validate one Human Review display row."""

    if not isinstance(value, DashboardHumanReviewRow):
        raise DashboardValidationError(
            "value must be a DashboardHumanReviewRow."
        )
    _require_project_id(value.project_id)
    for label, text in (
        ("human_review_decision_id", value.human_review_decision_id),
        ("target_type", value.target_type),
        ("target_id", value.target_id),
        ("reference_validation_status", value.reference_validation_status),
        ("review_mode", value.review_mode),
        ("decision", value.decision),
        ("reviewer_identity", value.reviewer_identity),
        ("decided_at", value.decided_at),
    ):
        _require_trimmed_text(text, label)
    _require_sha256(value.target_content_fingerprint)
    if value.reference_validation_fingerprint is not None:
        _require_sha256(value.reference_validation_fingerprint)
    _optional_trimmed_text(value.rationale, "rationale")
    _require_sha256(value.decision_fingerprint)
    validate_dashboard_status(value.status)
    if value.status.state != value.decision:
        raise DashboardValidationError(
            "Human Review status must preserve the exact decision."
        )
    validate_evidence_navigation(value.evidence)
    if any(
        reference.project_id != value.project_id
        for reference in value.evidence.references
    ):
        raise DashboardValidationError(
            "Human Review evidence belongs to another project."
        )
    return value


def make_attention_review_view(
    *,
    project_id: str,
    reviews: Iterable[DashboardHumanReviewRow],
    issues: Iterable[DashboardIssueView],
) -> DashboardAttentionReviewView:
    """Create the deterministic Attention and Human Review view."""

    review_tuple = tuple(reviews)
    issue_tuple = tuple(issues)
    for item in review_tuple:
        validate_human_review_row(item)
    for item in issue_tuple:
        validate_issue_view(item)
    _require_unique(
        (item.human_review_decision_id for item in review_tuple),
        "human_review_decision_id",
    )
    _require_unique((item.issue_code for item in issue_tuple), "issue_code")
    latest_exact: dict[
        tuple[str, str, str, str | None],
        DashboardHumanReviewRow,
    ] = {}
    for review in sorted(
        review_tuple,
        key=lambda item: (
            item.decided_at,
            item.human_review_decision_id,
        ),
    ):
        latest_exact[
            (
                review.target_type,
                review.target_id,
                review.target_content_fingerprint,
                review.reference_validation_fingerprint,
            )
        ] = review
    current_reviews = tuple(latest_exact.values())
    has_blocking = any(
        issue.issue_level == "blocking" for issue in issue_tuple
    ) or any(
        review.decision == "reject"
        for review in current_reviews
    )
    has_attention = has_blocking or bool(issue_tuple) or any(
        review.decision == "request_changes"
        for review in current_reviews
    )
    state = "blocking" if has_blocking else (
        "attention_required" if has_attention else "clear"
    )
    view = DashboardAttentionReviewView(
        project_id=_require_project_id(project_id),
        status=present_status(state),
        reviews=tuple(
            sorted(
                review_tuple,
                key=lambda item: (
                    item.decided_at,
                    item.human_review_decision_id,
                ),
                reverse=True,
            )
        ),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda item: (
                    0 if item.issue_level == "blocking" else 1,
                    item.issue_code,
                ),
            )
        ),
    )
    return validate_attention_review_view(view)


def validate_attention_review_view(
    value: object,
) -> DashboardAttentionReviewView:
    """Validate the Attention and Human Review view."""

    if not isinstance(value, DashboardAttentionReviewView):
        raise DashboardValidationError(
            "value must be a DashboardAttentionReviewView."
        )
    _require_project_id(value.project_id)
    validate_dashboard_status(value.status)
    for item in value.reviews:
        validate_human_review_row(item)
        if item.project_id != value.project_id:
            raise DashboardValidationError(
                "Human Review row belongs to another project."
            )
    for item in value.issues:
        validate_issue_view(item)
    _require_unique(
        (item.human_review_decision_id for item in value.reviews),
        "human_review_decision_id",
    )
    _require_unique((item.issue_code for item in value.issues), "issue_code")
    return value


def make_traceability_node(
    *,
    node_type: str,
    node_id: str,
    label: str,
    secondary_text: str | None = None,
    status: DashboardStatus | None = None,
    evidence_references: Iterable[EvidenceReference] = (),
) -> DashboardTraceabilityNode:
    """Create one canonical typed traceability node."""

    node_type_value = _require_trimmed_text(node_type, "node_type")
    if node_type_value not in DASHBOARD_TRACEABILITY_NODE_TYPES:
        raise DashboardValidationError(
            "node_type is not supported."
        )
    node_id_value = _require_trimmed_text(node_id, "node_id")
    node = DashboardTraceabilityNode(
        node_key=f"{node_type_value}:{node_id_value}",
        node_type=node_type_value,
        node_id=node_id_value,
        label=_require_trimmed_text(label, "label"),
        secondary_text=_optional_trimmed_text(
            secondary_text,
            "secondary_text",
        ),
        status=status,
        evidence=build_evidence_navigation(evidence_references),
    )
    return validate_traceability_node(node)


def validate_traceability_node(
    value: object,
) -> DashboardTraceabilityNode:
    """Validate one traceability graph node."""

    if not isinstance(value, DashboardTraceabilityNode):
        raise DashboardValidationError(
            "value must be a DashboardTraceabilityNode."
        )
    if value.node_type not in DASHBOARD_TRACEABILITY_NODE_TYPES:
        raise DashboardValidationError("node_type is not supported.")
    _require_trimmed_text(value.node_id, "node_id")
    if value.node_key != f"{value.node_type}:{value.node_id}":
        raise DashboardValidationError(
            "node_key must be derived from node_type and node_id."
        )
    _require_trimmed_text(value.label, "label")
    _optional_trimmed_text(value.secondary_text, "secondary_text")
    if value.status is not None:
        validate_dashboard_status(value.status)
    validate_evidence_navigation(value.evidence)
    return value


def make_traceability_edge(
    *,
    source_node_key: str,
    target_node_key: str,
    relationship: str,
    label: str,
) -> DashboardTraceabilityEdge:
    """Create one canonical directed traceability edge."""

    source = _require_trimmed_text(
        source_node_key,
        "source_node_key",
    )
    target = _require_trimmed_text(
        target_node_key,
        "target_node_key",
    )
    relation = _require_trimmed_text(
        relationship,
        "relationship",
    )
    edge = DashboardTraceabilityEdge(
        edge_key=f"{source}->{relation}->{target}",
        source_node_key=source,
        target_node_key=target,
        relationship=relation,
        label=_require_trimmed_text(label, "label"),
    )
    return validate_traceability_edge(edge)


def validate_traceability_edge(
    value: object,
) -> DashboardTraceabilityEdge:
    """Validate one traceability graph edge."""

    if not isinstance(value, DashboardTraceabilityEdge):
        raise DashboardValidationError(
            "value must be a DashboardTraceabilityEdge."
        )
    for label, text in (
        ("source_node_key", value.source_node_key),
        ("target_node_key", value.target_node_key),
        ("relationship", value.relationship),
        ("label", value.label),
    ):
        _require_trimmed_text(text, label)
    expected = (
        f"{value.source_node_key}->{value.relationship}->"
        f"{value.target_node_key}"
    )
    if value.edge_key != expected:
        raise DashboardValidationError(
            "edge_key must be derived from edge endpoints and relationship."
        )
    if value.source_node_key == value.target_node_key:
        raise DashboardValidationError(
            "traceability self-edges are not allowed."
        )
    return value


def make_traceability_view(
    *,
    project_id: str,
    nodes: Iterable[DashboardTraceabilityNode],
    edges: Iterable[DashboardTraceabilityEdge],
    issues: Iterable[DashboardIssueView] = (),
) -> DashboardTraceabilityView:
    """Create one deterministic project traceability graph."""

    node_tuple = tuple(nodes)
    edge_tuple = tuple(edges)
    issue_tuple = tuple(issues)
    for item in node_tuple:
        validate_traceability_node(item)
    for item in edge_tuple:
        validate_traceability_edge(item)
    for item in issue_tuple:
        validate_issue_view(item)
    _require_unique((item.node_key for item in node_tuple), "node_key")
    _require_unique((item.edge_key for item in edge_tuple), "edge_key")
    _require_unique((item.issue_code for item in issue_tuple), "issue_code")
    known = {item.node_key for item in node_tuple}
    for edge in edge_tuple:
        if (
            edge.source_node_key not in known
            or edge.target_node_key not in known
        ):
            raise DashboardValidationError(
                "traceability edge references an unknown node."
            )
    view = DashboardTraceabilityView(
        project_id=_require_project_id(project_id),
        nodes=tuple(
            sorted(
                node_tuple,
                key=lambda item: (
                    item.node_type,
                    item.label.casefold(),
                    item.node_id,
                ),
            )
        ),
        edges=tuple(
            sorted(
                edge_tuple,
                key=lambda item: (
                    item.source_node_key,
                    item.relationship,
                    item.target_node_key,
                ),
            )
        ),
        issues=tuple(
            sorted(
                issue_tuple,
                key=lambda item: (
                    0 if item.issue_level == "blocking" else 1,
                    item.issue_code,
                ),
            )
        ),
    )
    return validate_traceability_view(view)


def validate_traceability_view(
    value: object,
) -> DashboardTraceabilityView:
    """Validate one complete project traceability graph."""

    if not isinstance(value, DashboardTraceabilityView):
        raise DashboardValidationError(
            "value must be a DashboardTraceabilityView."
        )
    _require_project_id(value.project_id)
    for item in value.nodes:
        validate_traceability_node(item)
    for item in value.edges:
        validate_traceability_edge(item)
    for item in value.issues:
        validate_issue_view(item)
    _require_unique((item.node_key for item in value.nodes), "node_key")
    _require_unique((item.edge_key for item in value.edges), "edge_key")
    known = {item.node_key for item in value.nodes}
    if any(
        edge.source_node_key not in known
        or edge.target_node_key not in known
        for edge in value.edges
    ):
        raise DashboardValidationError(
            "traceability edge references an unknown node."
        )
    return value


def make_document_preview(
    *,
    project_id: str,
    reference: EvidenceReference,
    repository_relative_path: str,
    title: str,
    media_type: str,
    file_size_bytes: int,
    actual_sha256: str,
    fingerprint_status: str,
    render_mode: str,
    content_text: str | None,
    highlighted_text: str | None,
    table_columns: Iterable[str] = (),
    table_rows: Iterable[Iterable[str]] = (),
    selected_json_pointer: str | None = None,
    selected_table_row_key: str | None = None,
    truncated: bool = False,
    issue: str | None = None,
) -> DashboardDocumentPreview:
    """Create one safe immutable internal document preview payload."""

    preview = DashboardDocumentPreview(
        project_id=_require_project_id(project_id),
        reference=reference,
        repository_relative_path=_require_trimmed_text(
            repository_relative_path,
            "repository_relative_path",
        ),
        title=_require_trimmed_text(title, "title"),
        media_type=_require_trimmed_text(media_type, "media_type"),
        file_size_bytes=_require_non_negative_int(
            file_size_bytes,
            "file_size_bytes",
        ),
        actual_sha256=_require_sha256(actual_sha256),
        fingerprint_status=_require_trimmed_text(
            fingerprint_status,
            "fingerprint_status",
        ),
        render_mode=_require_trimmed_text(render_mode, "render_mode"),
        content_text=content_text,
        highlighted_text=highlighted_text,
        table_columns=tuple(
            _require_trimmed_text(item, "table_column")
            for item in table_columns
        ),
        table_rows=tuple(
            tuple(str(cell) for cell in row)
            for row in table_rows
        ),
        selected_json_pointer=selected_json_pointer,
        selected_table_row_key=selected_table_row_key,
        truncated=_require_bool(truncated, "truncated"),
        issue=issue,
    )
    return validate_document_preview(preview)


def validate_document_preview(
    value: object,
) -> DashboardDocumentPreview:
    """Validate one internal document viewer payload."""

    if not isinstance(value, DashboardDocumentPreview):
        raise DashboardValidationError(
            "value must be a DashboardDocumentPreview."
        )
    _require_project_id(value.project_id)
    if value.reference.project_id != value.project_id:
        raise DashboardValidationError(
            "document reference belongs to another project."
        )
    validate_evidence_navigation(
        build_evidence_navigation((value.reference,))
    )
    _require_trimmed_text(
        value.repository_relative_path,
        "repository_relative_path",
    )
    _require_trimmed_text(value.title, "title")
    _require_trimmed_text(value.media_type, "media_type")
    _require_non_negative_int(value.file_size_bytes, "file_size_bytes")
    _require_sha256(value.actual_sha256)
    if value.fingerprint_status not in DASHBOARD_FINGERPRINT_STATUSES:
        raise DashboardValidationError(
            "fingerprint_status is not supported."
        )
    if value.render_mode not in DASHBOARD_DOCUMENT_RENDER_MODES:
        raise DashboardValidationError(
            "render_mode is not supported."
        )
    if value.content_text is not None and not isinstance(
        value.content_text,
        str,
    ):
        raise DashboardValidationError(
            "content_text must be str or None."
        )
    if value.highlighted_text is not None and not isinstance(
        value.highlighted_text,
        str,
    ):
        raise DashboardValidationError(
            "highlighted_text must be str or None."
        )
    if not isinstance(value.table_columns, tuple):
        raise DashboardValidationError(
            "table_columns must be a tuple."
        )
    if not isinstance(value.table_rows, tuple) or any(
        not isinstance(row, tuple) for row in value.table_rows
    ):
        raise DashboardValidationError(
            "table_rows must be a tuple of tuples."
        )
    if value.render_mode == "table":
        if not value.table_columns:
            raise DashboardValidationError(
                "table preview requires columns."
            )
        if any(
            len(row) != len(value.table_columns)
            for row in value.table_rows
        ):
            raise DashboardValidationError(
                "table rows must match the column count."
            )
    elif value.table_columns or value.table_rows:
        raise DashboardValidationError(
            "non-table preview must not contain table data."
        )
    _require_bool(value.truncated, "truncated")
    _optional_trimmed_text(value.issue, "issue")
    return value
