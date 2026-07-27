"""Tests for P7 dashboard types, Evidence References and presenter foundation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import modules.project_dashboard as public_api
from modules.project_dashboard.errors import (
    DashboardIntegrityError,
    DashboardPresentationError,
    DashboardReferenceError,
    DashboardValidationError,
)
from modules.project_dashboard.presenter import (
    make_dashboard_value,
    make_issue_view,
    make_section_view,
    present_issue_status,
    present_status,
    status_semantic_for_state,
    supported_dashboard_states,
    validate_dashboard_status,
    validate_dashboard_value,
    validate_issue_view,
    validate_section_view,
)
from modules.project_dashboard.references import (
    build_evidence_navigation,
    canonicalize_evidence_references,
    evidence_reference_key,
    resolve_evidence_path,
    validate_evidence_location,
    validate_evidence_navigation,
    validate_evidence_reference,
)
from modules.project_dashboard.types import (
    DASHBOARD_EVIDENCE_ROLES,
    DASHBOARD_ISSUE_LEVELS,
    DASHBOARD_NAVIGATION_MODES,
    DASHBOARD_STATUS_SEMANTICS,
    DashboardIssueView,
    DashboardSectionView,
    DashboardStatus,
    DashboardValue,
    EvidenceLocation,
    EvidenceNavigation,
    EvidenceReference,
)


PROJECT_ID = "318604"


def reference(
    *,
    reference_type: str = "project_manifest",
    reference_id: str = "318604",
    label: str = "Project Manifest",
    path: str = "data/projects/318604/project.json",
    fingerprint: str | None = "a" * 64,
    media_type: str = "application/json",
    source_role: str | None = None,
    relationship: str = "describes",
    evidence_role: str = "direct",
    location: EvidenceLocation | None = None,
) -> EvidenceReference:
    return EvidenceReference(
        project_id=PROJECT_ID,
        reference_type=reference_type,
        reference_id=reference_id,
        display_label=label,
        repository_relative_path=path,
        content_fingerprint=fingerprint,
        media_type=media_type,
        source_role=source_role,
        relationship=relationship,
        evidence_role=evidence_role,
        location=location,
    )


def test_public_api_exports_foundation_contract() -> None:
    expected = {
        "EvidenceReference",
        "EvidenceNavigation",
        "DashboardStatus",
        "build_evidence_navigation",
        "resolve_evidence_path",
        "present_status",
        "make_dashboard_value",
    }
    assert expected.issubset(set(public_api.__all__))


@pytest.mark.parametrize(
    "value",
    (
        EvidenceLocation(),
        reference(),
        build_evidence_navigation(),
        present_status("covered"),
        make_dashboard_value(
            value_id="coverage",
            label="Coverage",
            primary_text="Covered",
        ),
        make_issue_view(
            issue_code="coverage.invalid_reference",
            message="Invalid reference.",
            issue_level="blocking",
        ),
        make_section_view(
            section_id="overview",
            title="Overview",
        ),
    ),
)
def test_foundation_types_are_frozen_and_slotted(value: object) -> None:
    assert value.__dataclass_params__.frozen is True
    assert value.__slots__
    field_name = value.__slots__[0]
    with pytest.raises(FrozenInstanceError):
        setattr(value, field_name, getattr(value, field_name))


def test_constant_sets_match_adr_status_contract() -> None:
    assert DASHBOARD_STATUS_SEMANTICS == {
        "neutral",
        "informational",
        "candidate",
        "reviewed",
        "attention",
        "blocking",
        "unavailable",
    }
    assert DASHBOARD_EVIDENCE_ROLES == {"direct", "contextual"}
    assert DASHBOARD_NAVIGATION_MODES == {
        "unavailable",
        "direct",
        "chooser",
    }
    assert DASHBOARD_ISSUE_LEVELS == {"warning", "blocking"}


@pytest.mark.parametrize(
    "location",
    (
        EvidenceLocation(),
        EvidenceLocation(section_anchor="Overview"),
        EvidenceLocation(line_start=4),
        EvidenceLocation(line_start=4, line_end=8),
        EvidenceLocation(json_pointer="/nodes/0"),
        EvidenceLocation(json_pointer=""),
        EvidenceLocation(table_row_key="SRC-000001"),
    ),
)
def test_valid_evidence_locations_are_accepted(
    location: EvidenceLocation,
) -> None:
    assert validate_evidence_location(location) is location


@pytest.mark.parametrize(
    "location",
    (
        EvidenceLocation(line_end=3),
        EvidenceLocation(line_start=0),
        EvidenceLocation(line_start=4, line_end=3),
        EvidenceLocation(json_pointer="nodes/0"),
        EvidenceLocation(section_anchor=" Overview"),
        EvidenceLocation(table_row_key=""),
        EvidenceLocation(
            line_start=1,
            json_pointer="/nodes/0",
        ),
    ),
)
def test_invalid_evidence_locations_are_rejected(
    location: EvidenceLocation,
) -> None:
    with pytest.raises(DashboardValidationError):
        validate_evidence_location(location)


def test_valid_evidence_reference_is_accepted() -> None:
    selected = reference(
        source_role="engineering_source",
        location=EvidenceLocation(json_pointer="/project_id"),
    )
    assert validate_evidence_reference(selected) is selected


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("project_id", "42"),
        ("reference_type", "Project Manifest"),
        ("reference_id", "bad id"),
        ("display_label", ""),
        ("repository_relative_path", "/absolute.json"),
        ("repository_relative_path", "../escape.json"),
        ("repository_relative_path", "data\\projects\\318604\\project.json"),
        ("content_fingerprint", "A" * 64),
        ("media_type", "json"),
        ("source_role", "unknown"),
        ("relationship", "Supports"),
        ("evidence_role", "primary"),
    ),
)
def test_invalid_evidence_reference_fields_are_rejected(
    field: str,
    value: object,
) -> None:
    data = {
        "project_id": PROJECT_ID,
        "reference_type": "project_manifest",
        "reference_id": PROJECT_ID,
        "display_label": "Project Manifest",
        "repository_relative_path": (
            "data/projects/318604/project.json"
        ),
        "content_fingerprint": "a" * 64,
        "media_type": "application/json",
        "source_role": None,
        "relationship": "describes",
        "evidence_role": "direct",
        "location": None,
    }
    data[field] = value
    selected = EvidenceReference(**data)
    with pytest.raises(DashboardValidationError):
        validate_evidence_reference(selected)


def test_project_local_path_cannot_cross_project_boundary() -> None:
    selected = reference(
        path="data/projects/999999/project.json"
    )
    with pytest.raises(DashboardValidationError):
        validate_evidence_reference(selected)


def test_global_repository_document_may_bind_selected_project() -> None:
    selected = reference(
        reference_type="framework_template",
        reference_id="TURING_RFLP_FRAMEWORK",
        path="context/frameworks/turing_rflp_framework.json",
    )
    assert validate_evidence_reference(selected) is selected


def test_reference_key_is_stable() -> None:
    assert evidence_reference_key(reference()) == evidence_reference_key(
        reference()
    )


def test_canonicalization_orders_direct_before_contextual() -> None:
    contextual = reference(
        reference_type="source_manifest",
        reference_id="SRC-000002",
        label="Context",
        path="data/projects/318604/sources/SRC-000002/source.json",
        evidence_role="contextual",
    )
    direct = reference(
        reference_type="source_manifest",
        reference_id="SRC-000001",
        label="Direct",
        path="data/projects/318604/sources/SRC-000001/source.json",
    )
    assert canonicalize_evidence_references(
        (contextual, direct)
    ) == (direct, contextual)


def test_exact_duplicate_references_are_deduplicated() -> None:
    selected = reference()
    assert canonicalize_evidence_references(
        (selected, selected)
    ) == (selected,)


def test_conflicting_duplicate_identity_is_rejected() -> None:
    first = reference(label="First")
    second = reference(label="Second")
    with pytest.raises(DashboardIntegrityError):
        canonicalize_evidence_references((first, second))


@pytest.mark.parametrize(
    ("count", "expected_mode"),
    (
        (0, "unavailable"),
        (1, "direct"),
        (2, "chooser"),
    ),
)
def test_navigation_mode_follows_reference_count(
    count: int,
    expected_mode: str,
) -> None:
    supplied = tuple(
        reference(
            reference_type="source_manifest",
            reference_id=f"SRC-{index:06d}",
            label=f"Source {index}",
            path=(
                "data/projects/318604/sources/"
                f"SRC-{index:06d}/source.json"
            ),
        )
        for index in range(1, count + 1)
    )
    assert build_evidence_navigation(supplied).mode == expected_mode


def test_manual_navigation_with_wrong_mode_is_rejected() -> None:
    selected = EvidenceNavigation(
        mode="chooser",
        references=(reference(),),
    )
    with pytest.raises(DashboardValidationError):
        validate_evidence_navigation(selected)


def test_resolve_existing_regular_file(tmp_path: Path) -> None:
    target = (
        tmp_path
        / "data"
        / "projects"
        / PROJECT_ID
        / "project.json"
    )
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")

    assert resolve_evidence_path(
        reference(),
        repository_root=tmp_path,
    ) == target.resolve()


def test_resolve_missing_file_fails_by_default(tmp_path: Path) -> None:
    with pytest.raises(DashboardReferenceError):
        resolve_evidence_path(
            reference(),
            repository_root=tmp_path,
        )


def test_resolve_missing_file_can_be_used_for_planning(
    tmp_path: Path,
) -> None:
    resolved = resolve_evidence_path(
        reference(),
        repository_root=tmp_path,
        require_exists=False,
    )
    assert resolved == (
        tmp_path
        / "data"
        / "projects"
        / PROJECT_ID
        / "project.json"
    ).resolve()


def test_symlink_in_evidence_path_is_rejected(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "data"
    link.symlink_to(actual, target_is_directory=True)

    with pytest.raises(DashboardReferenceError):
        resolve_evidence_path(
            reference(),
            repository_root=tmp_path,
            require_exists=False,
        )


def test_symlink_repository_root_is_rejected(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    root = tmp_path / "root"
    root.symlink_to(actual, target_is_directory=True)

    with pytest.raises(DashboardReferenceError):
        resolve_evidence_path(
            reference(),
            repository_root=root,
            require_exists=False,
        )


def test_non_directory_repository_root_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(DashboardReferenceError):
        resolve_evidence_path(
            reference(),
            repository_root=root,
            require_exists=False,
        )


@pytest.mark.parametrize(
    ("state", "semantic", "icon"),
    (
        ("uncovered", "unavailable", "—"),
        ("candidate_covered", "candidate", "◐"),
        ("reviewed_candidate_covered", "reviewed", "✓"),
        ("partially_covered", "attention", "!"),
        ("covered", "reviewed", "✓"),
        ("attention_required", "attention", "!"),
        ("not_supported", "unavailable", "—"),
        ("partially_supported", "attention", "!"),
        ("potentially_supported", "candidate", "◐"),
        ("not_available", "unavailable", "—"),
        ("processed", "reviewed", "✓"),
        ("invalidated", "blocking", "×"),
        ("confirm", "reviewed", "✓"),
        ("reject", "blocking", "×"),
    ),
)
def test_status_mapping_preserves_domain_meaning(
    state: str,
    semantic: str,
    icon: str,
) -> None:
    selected = present_status(state)
    assert selected.semantic == semantic
    assert selected.icon == icon
    assert selected.label


def test_potential_support_is_not_presented_as_ready() -> None:
    selected = present_status("potentially_supported")
    assert selected.label == "Potentially supported"
    assert "not approved" in (selected.explanation or "")
    assert selected.semantic == "candidate"


def test_unknown_status_is_rejected() -> None:
    with pytest.raises(DashboardPresentationError):
        present_status("generation_ready")


def test_status_semantic_accessor_uses_canonical_mapping() -> None:
    assert status_semantic_for_state("covered") == "reviewed"


def test_supported_states_are_sorted_and_complete() -> None:
    states = supported_dashboard_states()
    assert states == tuple(sorted(states))
    assert {
        "uncovered",
        "potentially_supported",
        "not_available",
        "processed",
        "confirm",
    }.issubset(states)


def test_status_semantic_cannot_be_changed_manually() -> None:
    selected = DashboardStatus(
        state="covered",
        label="Covered",
        semantic="blocking",
        icon="✓",
    )
    with pytest.raises(DashboardValidationError):
        validate_dashboard_status(selected)


def test_status_icon_cannot_be_changed_manually() -> None:
    selected = DashboardStatus(
        state="covered",
        label="Covered",
        semantic="reviewed",
        icon="!",
    )
    with pytest.raises(DashboardValidationError):
        validate_dashboard_status(selected)


def test_custom_status_label_and_explanation_are_allowed() -> None:
    selected = present_status(
        "not_available",
        label="Not assessed",
        explanation="Available from Phase G.",
    )
    assert selected.label == "Not assessed"
    assert selected.explanation == "Available from Phase G."


@pytest.mark.parametrize(
    ("issue_level", "semantic"),
    (
        ("warning", "attention"),
        ("blocking", "blocking"),
    ),
)
def test_issue_status_mapping(
    issue_level: str,
    semantic: str,
) -> None:
    assert present_issue_status(issue_level).semantic == semantic


def test_invalid_issue_level_is_rejected() -> None:
    with pytest.raises(DashboardPresentationError):
        present_issue_status("info")


def test_make_dashboard_value_binds_navigation() -> None:
    selected = make_dashboard_value(
        value_id="project_coverage",
        label="Project Coverage",
        primary_text="Covered",
        secondary_text="12 of 12 nodes",
        status=present_status("covered"),
        evidence_references=(reference(),),
    )
    assert selected.evidence.mode == "direct"
    assert validate_dashboard_value(selected) is selected


def test_dashboard_value_requires_trimmed_content() -> None:
    with pytest.raises(DashboardValidationError):
        make_dashboard_value(
            value_id="project_coverage",
            label=" Coverage",
            primary_text="Covered",
        )


def test_make_issue_view_accepts_namespaced_code() -> None:
    selected = make_issue_view(
        issue_code="repository_integration.invalid_reference",
        message="Reference invalid.",
        issue_level="blocking",
        evidence_references=(reference(),),
    )
    assert selected.status.semantic == "blocking"
    assert validate_issue_view(selected) is selected


def test_issue_status_must_match_issue_level() -> None:
    selected = DashboardIssueView(
        issue_code="coverage.warning",
        message="Warning.",
        issue_level="warning",
        status=present_status("blocking"),
        evidence=build_evidence_navigation(),
    )
    with pytest.raises(DashboardValidationError):
        validate_issue_view(selected)


def test_section_sorts_values_and_blocking_issues_first() -> None:
    a_value = make_dashboard_value(
        value_id="a_value",
        label="A",
        primary_text="A",
    )
    z_value = make_dashboard_value(
        value_id="z_value",
        label="Z",
        primary_text="Z",
    )
    warning = make_issue_view(
        issue_code="warning.issue",
        message="Warning.",
        issue_level="warning",
    )
    blocking = make_issue_view(
        issue_code="blocking.issue",
        message="Blocking.",
        issue_level="blocking",
    )

    selected = make_section_view(
        section_id="overview",
        title="Overview",
        values=(z_value, a_value),
        issues=(warning, blocking),
    )

    assert selected.values == (a_value, z_value)
    assert selected.issues == (blocking, warning)
    assert validate_section_view(selected) is selected


def test_section_rejects_duplicate_value_ids() -> None:
    selected = make_dashboard_value(
        value_id="same",
        label="Same",
        primary_text="One",
    )
    with pytest.raises(DashboardValidationError):
        make_section_view(
            section_id="overview",
            title="Overview",
            values=(selected, selected),
        )


def test_section_rejects_duplicate_issue_codes() -> None:
    selected = make_issue_view(
        issue_code="same.issue",
        message="Issue.",
        issue_level="warning",
    )
    with pytest.raises(DashboardValidationError):
        make_section_view(
            section_id="overview",
            title="Overview",
            issues=(selected, selected),
        )


def test_manual_unsorted_section_is_rejected() -> None:
    a_value = make_dashboard_value(
        value_id="a",
        label="A",
        primary_text="A",
    )
    z_value = make_dashboard_value(
        value_id="z",
        label="Z",
        primary_text="Z",
    )
    selected = DashboardSectionView(
        section_id="overview",
        title="Overview",
        description=None,
        values=(z_value, a_value),
        issues=(),
    )
    with pytest.raises(DashboardValidationError):
        validate_section_view(selected)
