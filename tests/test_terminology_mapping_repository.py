"""Tests for project-isolated terminology mapping persistence."""

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
from modules.terminology_mapping.errors import (
    DuplicateTerminologyMappingCandidateError,
    TerminologyMappingIntegrityError,
    TerminologyMappingPersistenceError,
    TerminologyMappingReferenceError,
)
from modules.terminology_mapping.repository import (
    SEMANTICS_DIRECTORY_NAME,
    TERMINOLOGY_MAPPINGS_DIRECTORY_NAME,
    TerminologyMappingRepository,
)

from tests.test_terminology_mapping_candidate_manifest import (
    consensus_outcome,
    consensus_result,
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
            raise TerminologyMappingReferenceError(
                "Information Unit not found."
            )
        return self.unit


def environment() -> tuple[
    TemporaryDirectory[str],
    Path,
    TerminologyMappingRepository,
]:
    temporary = TemporaryDirectory()
    root = Path(temporary.name) / "projects"
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Terminology Mapping Test")
    repository = TerminologyMappingRepository(
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
        TERMINOLOGY_MAPPINGS_DIRECTORY_NAME
        == "terminology_mappings"
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
            "TMC-000001",
        )

        assert created == loaded
        assert repository.list_candidates(PROJECT_ID) == (created,)
        assert repository.candidate_path(
            PROJECT_ID,
            "TMC-000001",
        ) == (
            root
            / PROJECT_ID
            / "semantics"
            / "terminology_mappings"
            / "TMC-000001.json"
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
            confidence="high",
            review_required=True,
        )
        second = repository.create_candidate(
            consensus_result(second_outcome),
            second_outcome,
        )

        assert first.terminology_mapping_candidate_id == "TMC-000001"
        assert second.terminology_mapping_candidate_id == "TMC-000002"
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
            DuplicateTerminologyMappingCandidateError
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
            / "terminology_mappings"
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
            / "terminology_mappings"
        )
        directory.mkdir(parents=True)
        (directory / "TMC-000001.json").write_text(
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
            "TMC-000001",
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["confidence_rationale"] = "Tampered."
        path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        with pytest.raises(TerminologyMappingIntegrityError):
            repository.load_candidate(
                PROJECT_ID,
                "TMC-000001",
            )
    finally:
        temporary.cleanup()


def test_missing_candidate_is_rejected() -> None:
    temporary, _, repository = environment()
    try:
        with pytest.raises(TerminologyMappingReferenceError):
            repository.load_candidate(
                PROJECT_ID,
                "TMC-000001",
            )
    finally:
        temporary.cleanup()


def test_occurrence_must_match_information_unit() -> None:
    temporary, _, repository = environment()
    try:
        outcome = consensus_outcome()
        changed_occurrence = replace(
            outcome.occurrence,
            term_text="valv",
        )
        changed_outcome = replace(
            outcome,
            occurrence=changed_occurrence,
        )

        with pytest.raises(TerminologyMappingReferenceError):
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
            project_semantics / "terminology_mappings"
        )
        try:
            mapping_directory.symlink_to(
                target,
                target_is_directory=True,
            )
        except OSError:
            pytest.skip("Symlinks are unavailable.")

        with pytest.raises(TerminologyMappingPersistenceError):
            repository.list_candidates(PROJECT_ID)

        scan = repository.scan_candidates(PROJECT_ID)
        assert scan.candidates == ()
        assert len(scan.issues) == 1
        assert scan.issues[0].code == "unsafe_mapping_directory"
    finally:
        temporary.cleanup()