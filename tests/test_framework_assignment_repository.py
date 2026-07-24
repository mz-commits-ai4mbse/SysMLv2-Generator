"""Tests for project-isolated framework-assignment persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.project_workspace import ProjectWorkspace
from modules.framework_assignment.errors import (
    DuplicateFrameworkAssignmentCandidateError,
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentPersistenceError,
    FrameworkAssignmentReferenceError,
)
from modules.framework_assignment.repository import (
    SEMANTICS_DIRECTORY_NAME,
    FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME,
    FrameworkAssignmentRepository,
)

from tests.test_framework_assignment_candidate_manifest import (
    consensus_result,
    outcome as consensus_outcome,
    proposal,
)


PROJECT_ID = "318604"


def fixed_clock() -> datetime:
    return datetime(
        2026,
        7,
        24,
        15,
        0,
        0,
        tzinfo=timezone.utc,
    )


def information_unit() -> InformationUnit:
    statement = "The pump shall preserve system pressure."
    return InformationUnit(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        information_unit_id="IU-000001",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=len(statement),
            ),
        ),
        source_excerpt=statement,
        interpreted_statement=statement,
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=(
            InformationUnitExtractionProvenance(
                team_id="semantic-team",
                persona_ids=("persona-a", "persona-b"),
                llm_provider="test-provider",
                llm_model="test-model",
                prompt_schema_version="1.0.0",
                consensus_report_id="CONSENSUS-TEST-001",
            )
        ),
        confidence="high",
        confidence_rationale="Unanimous semantic extraction.",
        content_fingerprint="a" * 64,
        created_at="2026-07-24T12:00:00Z",
    )


class FakeInformationUnitRepository:
    def __init__(self, unit: InformationUnit) -> None:
        self.unit = unit

    def load_information_unit(
        self,
        project_id: str,
        information_unit_id: str,
    ) -> InformationUnit:
        if (
            project_id != self.unit.project_id
            or information_unit_id
            != self.unit.information_unit_id
        ):
            raise FrameworkAssignmentReferenceError(
                "Information Unit not found."
            )
        return self.unit


def environment() -> tuple[
    TemporaryDirectory[str],
    Path,
    FrameworkAssignmentRepository,
]:
    temporary = TemporaryDirectory()
    root = Path(temporary.name) / "projects"
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Framework Assignment Test")
    repository = FrameworkAssignmentRepository(
        root=root,
        clock=fixed_clock,
        information_unit_repository=(
            FakeInformationUnitRepository(information_unit())
        ),
    )
    return temporary, root, repository


def test_persistence_directory_contract_is_explicit() -> None:
    assert SEMANTICS_DIRECTORY_NAME == "semantics"
    assert (
        FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME
        == "framework_assignments"
    )


def test_create_load_and_list_candidate() -> None:
    temporary, root, repository = environment()
    try:
        outcome = consensus_outcome()
        created = repository.create_candidate(
            consensus_result(outcome),
            outcome,
        )
        loaded = repository.load_candidate(
            PROJECT_ID,
            "FAC-000001",
        )

        assert created == loaded
        assert repository.list_candidates(PROJECT_ID) == (created,)
        assert repository.candidate_path(
            PROJECT_ID,
            "FAC-000001",
        ) == (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
            / "FAC-000001.json"
        )
    finally:
        temporary.cleanup()


def test_repository_allocates_sequential_ids() -> None:
    temporary, _, repository = environment()
    try:
        first_outcome = consensus_outcome()
        first = repository.create_candidate(
            consensus_result(first_outcome),
            first_outcome,
        )
        second_outcome = consensus_outcome(
            status="conflict",
            proposals=(
                proposal("FW_SYSTEM_REQUIREMENTS"),
                proposal("FW_SYSTEM_FUNCTIONAL"),
            ),
            confidence="high",
            review_required=True,
        )
        second = repository.create_candidate(
            consensus_result(second_outcome),
            second_outcome,
        )

        assert first.framework_assignment_candidate_id == "FAC-000001"
        assert second.framework_assignment_candidate_id == "FAC-000002"
    finally:
        temporary.cleanup()


def test_duplicate_professional_content_is_rejected() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        repository.create_candidate(
            consensus_result(outcome),
            outcome,
        )

        with pytest.raises(
            DuplicateFrameworkAssignmentCandidateError
        ):
            repository.create_candidate(
                consensus_result(outcome),
                outcome,
            )
    finally:
        temporary.cleanup()


def test_filter_by_information_unit_id() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        created = repository.create_candidate(
            consensus_result(outcome),
            outcome,
        )

        assert repository.list_candidates(
            PROJECT_ID,
            information_unit_id="IU-000001",
        ) == (created,)
        assert repository.list_candidates(
            PROJECT_ID,
            information_unit_id="IU-000002",
        ) == ()
    finally:
        temporary.cleanup()


def test_scan_reports_valid_candidate() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        created = repository.create_candidate(
            consensus_result(outcome),
            outcome,
        )
        scan = repository.scan_candidates(PROJECT_ID)

        assert scan.candidates == (created,)
        assert scan.issues == ()
    finally:
        temporary.cleanup()


def test_scan_reports_unexpected_entry() -> None:
    temporary, root, repository = environment()
    try:
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        directory.mkdir(parents=True)
        (directory / "notes.txt").write_text(
            "unexpected",
            encoding="utf-8",
        )
        scan = repository.scan_candidates(PROJECT_ID)

        assert scan.candidates == ()
        assert len(scan.issues) == 1
        assert scan.issues[0].code == "unexpected_mapping_entry"
    finally:
        temporary.cleanup()


def test_scan_reports_invalid_json() -> None:
    temporary, root, repository = environment()
    try:
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        directory.mkdir(parents=True)
        (directory / "FAC-000001.json").write_text(
            "{invalid",
            encoding="utf-8",
        )
        scan = repository.scan_candidates(PROJECT_ID)

        assert scan.candidates == ()
        assert scan.issues[0].code == "invalid_mapping_candidate"
    finally:
        temporary.cleanup()


def test_tampered_candidate_is_rejected_on_load() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        repository.create_candidate(
            consensus_result(outcome),
            outcome,
        )
        path = repository.candidate_path(
            PROJECT_ID,
            "FAC-000001",
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["confidence_rationale"] = "Tampered."
        path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        with pytest.raises(FrameworkAssignmentIntegrityError):
            repository.load_candidate(
                PROJECT_ID,
                "FAC-000001",
            )
    finally:
        temporary.cleanup()


def test_missing_candidate_is_rejected() -> None:
    temporary, _, repository = environment()
    try:
        with pytest.raises(FrameworkAssignmentReferenceError):
            repository.load_candidate(
                PROJECT_ID,
                "FAC-000001",
            )
    finally:
        temporary.cleanup()


def test_information_unit_fingerprint_must_match() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        changed_basis = replace(
            outcome.selected_proposals[0]
            .assignment_bases[0],
            reference_version="f" * 64,
        )
        changed_proposal = replace(
            outcome.selected_proposals[0],
            assignment_bases=(changed_basis,),
        )
        changed_outcome = replace(
            outcome,
            selected_proposals=(changed_proposal,),
        )

        with pytest.raises(FrameworkAssignmentReferenceError):
            repository.create_candidate(
                consensus_result(changed_outcome),
                changed_outcome,
            )
    finally:
        temporary.cleanup()


def test_symlink_mapping_directory_is_rejected() -> None:
    temporary, root, repository = environment()
    try:
        project_semantics = (
            root / PROJECT_ID / "semantics"
        )
        project_semantics.mkdir()
        target = Path(temporary.name) / "outside"
        target.mkdir()
        mapping_directory = (
            project_semantics / "framework_assignments"
        )
        try:
            mapping_directory.symlink_to(
                target,
                target_is_directory=True,
            )
        except OSError:
            pytest.skip("Symlinks are unavailable.")

        with pytest.raises(FrameworkAssignmentPersistenceError):
            repository.list_candidates(PROJECT_ID)

        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == ()
        assert len(scan.issues) == 1
        assert scan.issues[0].code == "unsafe_mapping_directory"
    finally:
        temporary.cleanup()


def test_persisted_json_is_deterministic_and_newline_terminated() -> None:
    temporary, _, repository = environment()
    try:
        selected = consensus_outcome()
        created = repository.create_candidate(
            consensus_result(selected),
            selected,
        )
        path = repository.candidate_path(
            PROJECT_ID,
            created.framework_assignment_candidate_id,
        )
        text = path.read_text(encoding="utf-8")

        assert text.endswith("\n")
        assert json.loads(text)["content_fingerprint"] == (
            created.content_fingerprint
        )
    finally:
        temporary.cleanup()


def test_empty_repository_lists_and_scans_cleanly() -> None:
    temporary, _, repository = environment()
    try:
        assert repository.list_candidates(PROJECT_ID) == ()
        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == ()
        assert scan.issues == ()
    finally:
        temporary.cleanup()


def test_list_ignores_unrecognized_entries_but_scan_reports_them() -> None:
    temporary, root, repository = environment()
    try:
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        directory.mkdir(parents=True)
        (directory / "README.md").write_text(
            "not a candidate",
            encoding="utf-8",
        )

        assert repository.list_candidates(PROJECT_ID) == ()
        scan = repository.scan_candidates(PROJECT_ID)
        assert len(scan.issues) == 1
        assert scan.issues[0].path == directory / "README.md"
    finally:
        temporary.cleanup()


def test_candidate_file_symlink_is_rejected() -> None:
    temporary, root, repository = environment()
    try:
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        directory.mkdir(parents=True)
        outside = Path(temporary.name) / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        link = directory / "FAC-000001.json"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("Symlinks are unavailable.")

        with pytest.raises(FrameworkAssignmentPersistenceError):
            repository.candidate_path(
                PROJECT_ID,
                "FAC-000001",
            )
        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == ()
        assert scan.issues[0].code == "invalid_mapping_candidate"
    finally:
        temporary.cleanup()


def test_semantics_directory_symlink_is_rejected() -> None:
    temporary, root, repository = environment()
    try:
        target = Path(temporary.name) / "outside-semantics"
        target.mkdir()
        semantics = root / PROJECT_ID / "semantics"
        try:
            semantics.symlink_to(
                target,
                target_is_directory=True,
            )
        except OSError:
            pytest.skip("Symlinks are unavailable.")

        with pytest.raises(FrameworkAssignmentPersistenceError):
            repository.list_candidates(PROJECT_ID)
    finally:
        temporary.cleanup()


def test_mapping_path_that_is_a_file_is_diagnostic() -> None:
    temporary, root, repository = environment()
    try:
        semantics = root / PROJECT_ID / "semantics"
        semantics.mkdir()
        path = semantics / "framework_assignments"
        path.write_text("not a directory", encoding="utf-8")

        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == ()
        assert scan.issues[0].code == "unsafe_mapping_directory"
    finally:
        temporary.cleanup()


def test_temporary_publication_collision_is_rejected() -> None:
    temporary, root, repository = environment()
    try:
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        directory.mkdir(parents=True)
        temporary_path = directory / ".FAC-000001.json.tmp"
        temporary_path.write_text("occupied", encoding="utf-8")
        selected = consensus_outcome()

        with pytest.raises(FrameworkAssignmentPersistenceError):
            repository.create_candidate(
                consensus_result(selected),
                selected,
            )
        assert not (directory / "FAC-000001.json").exists()
    finally:
        temporary.cleanup()


@pytest.mark.parametrize(
    "clock_value",
    (
        "not-a-datetime",
        datetime(2026, 7, 24, 15, 0, 0),
    ),
)
def test_invalid_clock_is_rejected(clock_value: object) -> None:
    temporary = TemporaryDirectory()
    try:
        root = Path(temporary.name) / "projects"
        workspace = ProjectWorkspace(
            root=root,
            id_generator=lambda: PROJECT_ID,
            clock=fixed_clock,
        )
        workspace.create_project("Clock Test")
        repository = FrameworkAssignmentRepository(
            root=root,
            clock=lambda: clock_value,
            information_unit_repository=(
                FakeInformationUnitRepository(information_unit())
            ),
        )
        selected = consensus_outcome()

        with pytest.raises(FrameworkAssignmentPersistenceError):
            repository.create_candidate(
                consensus_result(selected),
                selected,
            )
    finally:
        temporary.cleanup()


def test_consensus_and_information_unit_source_mismatch() -> None:
    temporary = TemporaryDirectory()
    try:
        root = Path(temporary.name) / "projects"
        workspace = ProjectWorkspace(
            root=root,
            id_generator=lambda: PROJECT_ID,
            clock=fixed_clock,
        )
        workspace.create_project("Mismatch Test")
        changed = replace(
            information_unit(),
            source_id="SRC-000999",
        )
        repository = FrameworkAssignmentRepository(
            root=root,
            clock=fixed_clock,
            information_unit_repository=(
                FakeInformationUnitRepository(changed)
            ),
        )
        selected = consensus_outcome()

        with pytest.raises(FrameworkAssignmentReferenceError):
            repository.create_candidate(
                consensus_result(selected),
                selected,
            )
    finally:
        temporary.cleanup()


@pytest.mark.parametrize(
    "candidate_id",
    (
        "FAC-000000",
        "FAC-00001",
        "TMC-000001",
        "../FAC-000001",
        None,
    ),
)
def test_invalid_candidate_path_id_is_rejected(
    candidate_id: object,
) -> None:
    temporary, _, repository = environment()
    try:
        with pytest.raises(Exception):
            repository.candidate_path(
                PROJECT_ID,
                candidate_id,
            )
    finally:
        temporary.cleanup()


def test_scan_keeps_valid_candidates_beside_bad_entries() -> None:
    temporary, root, repository = environment()
    try:
        selected = consensus_outcome()
        created = repository.create_candidate(
            consensus_result(selected),
            selected,
        )
        directory = (
            root
            / PROJECT_ID
            / "semantics"
            / "framework_assignments"
        )
        (directory / "notes.txt").write_text(
            "unexpected",
            encoding="utf-8",
        )

        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == (created,)
        assert len(scan.issues) == 1
    finally:
        temporary.cleanup()