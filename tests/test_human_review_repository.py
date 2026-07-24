"""Tests for project-isolated Human Review persistence and gates."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from modules.human_review.errors import (
    DuplicateHumanReviewDecisionError,
    HumanReviewIntegrityError,
    HumanReviewPersistenceError,
    HumanReviewReferenceError,
    HumanReviewValidationError,
)
from modules.human_review.manifest import (
    create_human_review_target_snapshot,
)
from modules.human_review.repository import (
    HUMAN_REVIEWS_DIRECTORY_NAME,
    SEMANTICS_DIRECTORY_NAME,
    HumanReviewRepository,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
CONTENT_HASH = "a" * 64
VALIDATION_HASH = "b" * 64


def fixed_clock() -> datetime:
    return datetime(2026, 7, 24, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def projects_root(tmp_path: Path) -> Path:
    root = tmp_path / "projects"
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Human Review Test")
    return root


@pytest.fixture
def repository(projects_root: Path) -> HumanReviewRepository:
    return HumanReviewRepository(root=projects_root, clock=fixed_clock)


def target(
    *,
    target_type: str = "framework_assignment_candidate",
    target_id: str = "FAC-000001",
    fingerprint: str = CONTENT_HASH,
    recommended_mode: str = "quick_confirmation",
    validation_status: str = "valid",
    validation_fingerprint: str | None = VALIDATION_HASH,
):
    return create_human_review_target_snapshot(
        target_type=target_type,
        target_id=target_id,
        target_content_fingerprint=fingerprint,
        recommended_review_mode=recommended_mode,
        confirmation_required=True,
        reference_validation_status=validation_status,
        reference_validation_fingerprint=validation_fingerprint,
    )


def record(
    repository: HumanReviewRepository,
    *,
    selected_target=None,
    review_mode: str = "quick_confirmation",
    decision: str = "confirm",
    reviewer_identity: str = "moritz",
    rationale: str | None = None,
):
    return repository.record_decision(
        PROJECT_ID,
        target() if selected_target is None else selected_target,
        review_mode=review_mode,
        decision=decision,
        reviewer_identity=reviewer_identity,
        rationale=rationale,
    )


def test_directory_constants() -> None:
    assert SEMANTICS_DIRECTORY_NAME == "semantics"
    assert HUMAN_REVIEWS_DIRECTORY_NAME == "human_reviews"


def test_record_load_and_path(
    repository: HumanReviewRepository,
) -> None:
    item = record(repository)
    assert item.human_review_decision_id == "HRD-000001"
    assert repository.load_decision(
        PROJECT_ID,
        "HRD-000001",
    ) == item
    assert repository.decision_path(
        PROJECT_ID,
        "HRD-000001",
    ).parts[-4:] == (
        PROJECT_ID,
        "semantics",
        "human_reviews",
        "HRD-000001.json",
    )


def test_persisted_json_is_valid(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    data = json.loads(
        repository.decision_path(
            PROJECT_ID,
            "HRD-000001",
        ).read_text(encoding="utf-8")
    )
    assert data["decision"] == "confirm"


def test_ids_are_monotonic(
    repository: HumanReviewRepository,
) -> None:
    first = record(repository)
    second = record(
        repository,
        selected_target=target(target_id="FAC-000002"),
    )
    assert first.human_review_decision_id == "HRD-000001"
    assert second.human_review_decision_id == "HRD-000002"


def test_list_is_sorted(
    repository: HumanReviewRepository,
) -> None:
    record(repository, selected_target=target(target_id="FAC-000002"))
    record(repository)
    assert [
        item.human_review_decision_id
        for item in repository.list_decisions(PROJECT_ID)
    ] == ["HRD-000001", "HRD-000002"]


@pytest.mark.parametrize(
    ("target_type", "target_id", "status", "validation"),
    [
        (
            "information_unit_publication",
            "IU-000001",
            "not_applicable",
            None,
        ),
        (
            "terminology_mapping_candidate",
            "TMC-000001",
            "valid",
            VALIDATION_HASH,
        ),
        (
            "framework_assignment_candidate",
            "FAC-000001",
            "valid",
            VALIDATION_HASH,
        ),
    ],
)
def test_all_target_types_persist(
    repository,
    target_type,
    target_id,
    status,
    validation,
) -> None:
    item = record(
        repository,
        selected_target=target(
            target_type=target_type,
            target_id=target_id,
            validation_status=status,
            validation_fingerprint=validation,
        ),
    )
    assert item.target.target_type == target_type


def test_filter_by_target_type(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    record(
        repository,
        selected_target=target(
            target_type="terminology_mapping_candidate",
            target_id="TMC-000001",
        ),
    )
    items = repository.list_decisions(
        PROJECT_ID,
        target_type="terminology_mapping_candidate",
    )
    assert len(items) == 1
    assert items[0].target.target_id == "TMC-000001"


def test_filter_by_exact_target(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    record(repository, selected_target=target(target_id="FAC-000002"))
    items = repository.list_decisions(
        PROJECT_ID,
        target_type="framework_assignment_candidate",
        target_id="FAC-000002",
    )
    assert len(items) == 1


def test_target_id_filter_requires_type(
    repository: HumanReviewRepository,
) -> None:
    with pytest.raises(HumanReviewValidationError):
        repository.list_decisions(PROJECT_ID, target_id="FAC-000001")


@pytest.mark.parametrize(
    ("target_type", "target_id"),
    [
        ("unknown", None),
        ("framework_assignment_candidate", "TMC-000001"),
        ("framework_assignment_candidate", "FAC-1"),
        ("terminology_mapping_candidate", "FAC-000001"),
    ],
)
def test_invalid_filters_are_rejected(
    repository,
    target_type,
    target_id,
) -> None:
    with pytest.raises(HumanReviewValidationError):
        repository.list_decisions(
            PROJECT_ID,
            target_type=target_type,
            target_id=target_id,
        )


def test_duplicate_decision_is_rejected(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    with pytest.raises(DuplicateHumanReviewDecisionError):
        record(repository)


def test_different_reviewer_is_not_duplicate(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    second = record(repository, reviewer_identity="second-reviewer")
    assert second.human_review_decision_id == "HRD-000002"


def test_missing_decision_is_rejected(
    repository: HumanReviewRepository,
) -> None:
    with pytest.raises(HumanReviewReferenceError):
        repository.load_decision(PROJECT_ID, "HRD-000001")


def test_unknown_project_is_rejected(tmp_path: Path) -> None:
    repository = HumanReviewRepository(root=tmp_path, clock=fixed_clock)
    with pytest.raises(Exception):
        repository.list_decisions(PROJECT_ID)


def test_require_confirmation_returns_exact_decision(
    repository: HumanReviewRepository,
) -> None:
    saved = record(repository)
    confirmed = repository.require_confirmation(
        PROJECT_ID,
        target_type="framework_assignment_candidate",
        target_id="FAC-000001",
        target_content_fingerprint=CONTENT_HASH,
        reference_validation_fingerprint=VALIDATION_HASH,
    )
    assert confirmed == saved


@pytest.mark.parametrize(
    ("target_id", "content_hash", "validation_hash"),
    [
        ("FAC-000002", CONTENT_HASH, VALIDATION_HASH),
        ("FAC-000001", "c" * 64, VALIDATION_HASH),
        ("FAC-000001", CONTENT_HASH, "d" * 64),
        ("FAC-000001", "c" * 64, "d" * 64),
    ],
)
def test_gate_rejects_non_exact_binding(
    repository,
    target_id,
    content_hash,
    validation_hash,
) -> None:
    record(repository)
    with pytest.raises(HumanReviewReferenceError):
        repository.require_confirmation(
            PROJECT_ID,
            target_type="framework_assignment_candidate",
            target_id=target_id,
            target_content_fingerprint=content_hash,
            reference_validation_fingerprint=validation_hash,
        )


@pytest.mark.parametrize("selected", ["reject", "request_changes"])
def test_latest_non_confirmation_blocks_gate(
    repository,
    selected,
) -> None:
    record(repository)
    record(
        repository,
        review_mode="detailed_review",
        decision=selected,
        rationale="Human correction required.",
    )
    with pytest.raises(HumanReviewIntegrityError):
        repository.require_confirmation(
            PROJECT_ID,
            target_type="framework_assignment_candidate",
            target_id="FAC-000001",
            target_content_fingerprint=CONTENT_HASH,
            reference_validation_fingerprint=VALIDATION_HASH,
        )


def test_newer_confirmation_supersedes_rejection(
    repository: HumanReviewRepository,
) -> None:
    record(
        repository,
        review_mode="detailed_review",
        decision="reject",
        rationale="First review rejected.",
    )
    record(repository)
    assert repository.require_confirmation(
        PROJECT_ID,
        target_type="framework_assignment_candidate",
        target_id="FAC-000001",
        target_content_fingerprint=CONTENT_HASH,
        reference_validation_fingerprint=VALIDATION_HASH,
    ).decision == "confirm"


def test_information_unit_gate_accepts_no_validation_fingerprint(
    repository: HumanReviewRepository,
) -> None:
    record(
        repository,
        selected_target=target(
            target_type="information_unit_publication",
            target_id="IU-000001",
            validation_status="not_applicable",
            validation_fingerprint=None,
        ),
    )
    assert repository.require_confirmation(
        PROJECT_ID,
        target_type="information_unit_publication",
        target_id="IU-000001",
        target_content_fingerprint=CONTENT_HASH,
        reference_validation_fingerprint=None,
    ).decision == "confirm"


@pytest.mark.parametrize(
    ("content_hash", "validation_hash"),
    [
        ("bad", VALIDATION_HASH),
        (CONTENT_HASH, "bad"),
        (None, VALIDATION_HASH),
        (CONTENT_HASH, 1),
    ],
)
def test_gate_rejects_invalid_fingerprint_input(
    repository,
    content_hash,
    validation_hash,
) -> None:
    with pytest.raises(HumanReviewValidationError):
        repository.require_confirmation(
            PROJECT_ID,
            target_type="framework_assignment_candidate",
            target_id="FAC-000001",
            target_content_fingerprint=content_hash,
            reference_validation_fingerprint=validation_hash,
        )


def test_scan_empty_repository(
    repository: HumanReviewRepository,
) -> None:
    result = repository.scan_decisions(PROJECT_ID)
    assert result.decisions == ()
    assert result.issues == ()


def test_scan_valid_repository(
    repository: HumanReviewRepository,
) -> None:
    saved = record(repository)
    result = repository.scan_decisions(PROJECT_ID)
    assert result.decisions == (saved,)
    assert result.issues == ()


def test_scan_reports_unexpected_entry(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    directory = repository.decision_path(
        PROJECT_ID,
        "HRD-000001",
    ).parent
    (directory / "README.txt").write_text("unexpected", encoding="utf-8")
    result = repository.scan_decisions(PROJECT_ID)
    assert result.decisions
    assert result.issues[0].code == "unexpected_review_entry"


def test_scan_reports_invalid_json(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    repository.decision_path(
        PROJECT_ID,
        "HRD-000001",
    ).write_text("{invalid", encoding="utf-8")
    result = repository.scan_decisions(PROJECT_ID)
    assert result.decisions == ()
    assert result.issues[0].code == "invalid_review_decision"


def test_load_detects_tampering(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    path = repository.decision_path(PROJECT_ID, "HRD-000001")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reviewer_identity"] = "attacker"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(HumanReviewIntegrityError):
        repository.load_decision(PROJECT_ID, "HRD-000001")


def test_load_detects_project_mismatch(
    repository: HumanReviewRepository,
) -> None:
    record(repository)
    path = repository.decision_path(PROJECT_ID, "HRD-000001")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["project_id"] = "654321"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(Exception):
        repository.load_decision(PROJECT_ID, "HRD-000001")


def test_symlink_decision_is_rejected(
    repository: HumanReviewRepository,
    tmp_path: Path,
) -> None:
    path = repository.decision_path(PROJECT_ID, "HRD-000001")
    path.parent.mkdir(parents=True)
    external = tmp_path / "external.json"
    external.write_text("{}", encoding="utf-8")
    path.symlink_to(external)
    with pytest.raises(HumanReviewPersistenceError):
        repository.decision_path(PROJECT_ID, "HRD-000001")


def test_naive_clock_is_rejected(
    projects_root: Path,
) -> None:
    repository = HumanReviewRepository(
        root=projects_root,
        clock=lambda: datetime(2026, 7, 24, 18, 0),
    )
    with pytest.raises(HumanReviewPersistenceError):
        record(repository)


def test_non_datetime_clock_is_rejected(
    projects_root: Path,
) -> None:
    repository = HumanReviewRepository(
        root=projects_root,
        clock=lambda: "now",
    )
    with pytest.raises(HumanReviewPersistenceError):
        record(repository)


def test_record_rejects_non_target(
    repository: HumanReviewRepository,
) -> None:
    with pytest.raises(HumanReviewValidationError):
        record(repository, selected_target={})


@pytest.mark.parametrize(
    "bad_id",
    ["HRD-000000", "HRD-1", "FAC-000001", "../HRD-000001"],
)
def test_decision_path_rejects_invalid_id(repository, bad_id) -> None:
    with pytest.raises(HumanReviewValidationError):
        repository.decision_path(PROJECT_ID, bad_id)


def test_existing_target_file_blocks_publish(
    repository: HumanReviewRepository,
) -> None:
    path = repository.decision_path(PROJECT_ID, "HRD-000001")
    path.parent.mkdir(parents=True)
    path.write_text("occupied", encoding="utf-8")
    with pytest.raises(Exception):
        record(repository)


def test_target_file_is_never_overwritten(
    repository: HumanReviewRepository,
) -> None:
    path = repository.decision_path(PROJECT_ID, "HRD-000001")
    path.parent.mkdir(parents=True)
    path.write_text("preserve", encoding="utf-8")
    with pytest.raises(Exception):
        record(repository)
    assert path.read_text(encoding="utf-8") == "preserve"