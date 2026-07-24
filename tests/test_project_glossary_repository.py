"""Tests for persistent and isolated Project Glossary operations."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from modules.project_glossary.decision_manifest import (
    create_terminology_decision,
    terminology_decision_to_json,
)
from modules.project_glossary.errors import (
    AmbiguityGroupNotFoundError,
    DuplicatePreferredLabelError,
    InvalidTerminologyLifecycleTransitionError,
    ProjectConceptNotFoundError,
    ProjectGlossaryNotFoundError,
    ProjectGlossaryPersistenceError,
    ProjectGlossaryValidationError,
    TerminologyDecisionError,
    UnsafeProjectGlossaryPathError,
)
from modules.project_glossary.manifest import (
    project_glossary_from_json,
    project_glossary_to_json,
)
from modules.project_glossary.repository import (
    SEMANTICS_DIRECTORY_NAME,
    ProjectGlossaryRepository,
)
from modules.project_glossary.types import (
    LocalizedGlossaryText,
    ProjectConceptProvenance,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.errors import (
    ProjectNotFoundError,
)


PROJECT_ID = "318604"
SECOND_PROJECT_ID = "318605"
TIMESTAMP = "2026-07-23T12:00:00Z"


def fixed_clock() -> datetime:
    """Return one deterministic timezone-aware timestamp."""

    return datetime(
        2026,
        7,
        23,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )


@pytest.fixture
def projects_root(tmp_path: Path) -> Path:
    """Create one valid Project Workspace project."""

    workspace = ProjectWorkspace(
        root=tmp_path / "projects",
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project(
        "Project Glossary Repository Test"
    )
    return workspace.root


@pytest.fixture
def repository(
    projects_root: Path,
) -> ProjectGlossaryRepository:
    """Create and initialize one Project Glossary repository."""

    result = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    result.initialize_glossary(
        PROJECT_ID,
        default_language="de",
    )
    return result


@pytest.fixture
def provenance() -> tuple[
    ProjectConceptProvenance,
    ...,
]:
    """Return one valid engineering-source provenance record."""

    return (
        ProjectConceptProvenance(
            provenance_type="engineering_source",
            reference_id="SRC-000001",
            rationale="Source segment contains the term.",
            source_projection_id="SP-000001",
            segment_ids=("SEG-000001",),
        ),
    )


def localized(
    text: str,
    language: str = "de",
) -> tuple[LocalizedGlossaryText, ...]:
    """Return one localized-text tuple."""

    return (
        LocalizedGlossaryText(
            language=language,
            text=text,
        ),
    )


def create_candidate(
    repository: ProjectGlossaryRepository,
    provenance: tuple[
        ProjectConceptProvenance,
        ...,
    ],
    *,
    preferred_label: str = "Antrieb",
    definition: str = "Ein projektspezifischer Antrieb.",
    alternative_labels: tuple[
        LocalizedGlossaryText,
        ...,
    ] = (),
):
    """Create one valid candidate with concise defaults."""

    return repository.create_candidate_concept(
        PROJECT_ID,
        preferred_labels=localized(
            preferred_label
        ),
        alternative_labels=alternative_labels,
        definitions=localized(definition),
        provenance=provenance,
        rationale="Initial glossary candidate.",
    )


def test_semantics_directory_constant() -> None:
    assert SEMANTICS_DIRECTORY_NAME == "semantics"


def test_initialize_glossary(
    projects_root: Path,
) -> None:
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )

    glossary = repository.initialize_glossary(
        PROJECT_ID,
        default_language="de",
    )

    assert glossary.project_id == PROJECT_ID
    assert glossary.glossary_revision == 1
    assert glossary.default_language == "de"
    assert glossary.created_at == TIMESTAMP
    assert glossary.updated_at == TIMESTAMP
    assert glossary.concepts == ()
    assert glossary.ambiguity_groups == ()


def test_initialize_creates_expected_paths(
    repository: ProjectGlossaryRepository,
    projects_root: Path,
) -> None:
    assert repository.glossary_path(PROJECT_ID) == (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "project_glossary.json"
    )
    assert repository.glossary_path(
        PROJECT_ID
    ).is_file()
    assert repository.terminology_decisions_path(
        PROJECT_ID
    ).is_dir()


def test_initialize_persists_deterministic_json(
    repository: ProjectGlossaryRepository,
) -> None:
    glossary = repository.load_glossary(PROJECT_ID)
    path = repository.glossary_path(PROJECT_ID)

    assert path.read_text(
        encoding="utf-8"
    ) == project_glossary_to_json(glossary)


def test_initialize_removes_temporary_file(
    repository: ProjectGlossaryRepository,
) -> None:
    path = repository.glossary_path(PROJECT_ID)

    assert not (
        path.parent / f".{path.name}.tmp"
    ).exists()


def test_reinitialize_is_rejected_without_overwrite(
    repository: ProjectGlossaryRepository,
) -> None:
    before = repository.glossary_path(
        PROJECT_ID
    ).read_bytes()

    with pytest.raises(ProjectGlossaryPersistenceError):
        repository.initialize_glossary(
            PROJECT_ID,
            default_language="en",
        )

    assert repository.glossary_path(
        PROJECT_ID
    ).read_bytes() == before


def test_initialize_requires_existing_project(
    tmp_path: Path,
) -> None:
    repository = ProjectGlossaryRepository(
        root=tmp_path / "projects",
        clock=fixed_clock,
    )

    with pytest.raises(ProjectNotFoundError):
        repository.initialize_glossary(
            PROJECT_ID,
            default_language="de",
        )


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "12345",
        "1234567",
        "abcdef",
        "../318604",
        318604,
    ],
)
def test_repository_rejects_invalid_project_id(
    repository: ProjectGlossaryRepository,
    project_id: object,
) -> None:
    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.glossary_path(
            project_id  # type: ignore[arg-type]
        )


def test_load_missing_glossary(
    projects_root: Path,
) -> None:
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )

    with pytest.raises(ProjectGlossaryNotFoundError):
        repository.load_glossary(PROJECT_ID)


def test_load_rejects_invalid_glossary_json(
    repository: ProjectGlossaryRepository,
) -> None:
    repository.glossary_path(PROJECT_ID).write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(ProjectGlossaryValidationError):
        repository.load_glossary(PROJECT_ID)


def test_load_rejects_cross_project_glossary(
    repository: ProjectGlossaryRepository,
) -> None:
    path = repository.glossary_path(PROJECT_ID)
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    payload["project_id"] = SECOND_PROJECT_ID
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(ProjectGlossaryValidationError):
        repository.load_glossary(PROJECT_ID)


def test_load_rejects_glossary_directory(
    repository: ProjectGlossaryRepository,
) -> None:
    path = repository.glossary_path(PROJECT_ID)
    path.unlink()
    path.mkdir()

    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.load_glossary(PROJECT_ID)


def test_load_rejects_glossary_symlink(
    repository: ProjectGlossaryRepository,
    tmp_path: Path,
) -> None:
    path = repository.glossary_path(PROJECT_ID)
    target = tmp_path / "outside.json"
    target.write_text(
        path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path.unlink()
    path.symlink_to(target)

    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.load_glossary(PROJECT_ID)


def test_initialize_rejects_semantics_symlink(
    projects_root: Path,
    tmp_path: Path,
) -> None:
    semantics_path = (
        projects_root
        / PROJECT_ID
        / "semantics"
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    semantics_path.symlink_to(
        outside,
        target_is_directory=True,
    )
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )

    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.initialize_glossary(
            PROJECT_ID,
            default_language="de",
        )


def test_initialize_rejects_stale_temporary_file(
    projects_root: Path,
) -> None:
    semantics_path = (
        projects_root
        / PROJECT_ID
        / "semantics"
    )
    semantics_path.mkdir()
    temporary_path = (
        semantics_path / ".project_glossary.json.tmp"
    )
    temporary_path.write_text(
        "stale",
        encoding="utf-8",
    )
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )

    with pytest.raises(ProjectGlossaryPersistenceError):
        repository.initialize_glossary(
            PROJECT_ID,
            default_language="de",
        )


@pytest.mark.parametrize(
    "clock",
    [
        lambda: "not a datetime",
        lambda: datetime(2026, 7, 23, 12, 0, 0),
    ],
)
def test_repository_rejects_invalid_clock(
    projects_root: Path,
    clock,
) -> None:
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=clock,
    )

    with pytest.raises(ProjectGlossaryPersistenceError):
        repository.initialize_glossary(
            PROJECT_ID,
            default_language="de",
        )


def test_create_candidate_concept(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )

    assert concept.project_concept_id == "PC-000001"
    assert concept.latest_revision == 1
    assert len(concept.revisions) == 1
    assert (
        concept.revisions[0].lifecycle_status
        == "candidate"
    )
    assert (
        concept.revisions[0].preferred_labels[0].text
        == "Antrieb"
    )
    assert concept.revisions[0].provenance == provenance


def test_candidate_operation_increments_glossary_revision(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    assert repository.load_glossary(
        PROJECT_ID
    ).glossary_revision == 1

    create_candidate(repository, provenance)

    assert repository.load_glossary(
        PROJECT_ID
    ).glossary_revision == 2


def test_candidate_ids_are_sequential(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Antrieb",
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Motor",
    )
    third = create_candidate(
        repository,
        provenance,
        preferred_label="Getriebe",
    )

    assert [
        first.project_concept_id,
        second.project_concept_id,
        third.project_concept_id,
    ] == [
        "PC-000001",
        "PC-000002",
        "PC-000003",
    ]


def test_candidate_concepts_are_sorted(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    create_candidate(
        repository,
        provenance,
        preferred_label="Antrieb",
    )
    create_candidate(
        repository,
        provenance,
        preferred_label="Motor",
    )

    assert [
        concept.project_concept_id
        for concept in repository.load_glossary(
            PROJECT_ID
        ).concepts
    ] == [
        "PC-000001",
        "PC-000002",
    ]


def test_candidate_preferred_label_conflicts_are_allowed(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    create_candidate(
        repository,
        provenance,
        preferred_label="Port",
    )
    create_candidate(
        repository,
        provenance,
        preferred_label="PORT",
    )

    assert len(
        repository.load_glossary(
            PROJECT_ID
        ).concepts
    ) == 2


def test_create_candidate_accepts_generators(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = repository.create_candidate_concept(
        PROJECT_ID,
        preferred_labels=(
            value
            for value in localized("Antrieb")
        ),
        definitions=(
            value
            for value in localized(
                "Ein projektspezifischer Antrieb."
            )
        ),
        provenance=(
            value
            for value in provenance
        ),
        rationale="Generator candidate.",
    )

    assert concept.project_concept_id == "PC-000001"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("preferred_labels", ()),
        ("preferred_labels", ("Antrieb",)),
        ("definitions", ()),
        ("definitions", ("Definition",)),
        ("provenance", ()),
        ("provenance", ("SRC-000001",)),
        ("rationale", ""),
        ("rationale", " Candidate"),
    ],
)
def test_create_candidate_validates_content(
    repository: ProjectGlossaryRepository,
    provenance,
    field: str,
    value: object,
) -> None:
    arguments = {
        "preferred_labels": localized("Antrieb"),
        "definitions": localized(
            "Ein projektspezifischer Antrieb."
        ),
        "provenance": provenance,
        "rationale": "Initial candidate.",
    }
    arguments[field] = value

    with pytest.raises(ProjectGlossaryValidationError):
        repository.create_candidate_concept(
            PROJECT_ID,
            **arguments,
        )


def test_create_candidate_validates_relation_target(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        repository.create_candidate_concept(
            PROJECT_ID,
            preferred_labels=localized("Motor"),
            definitions=localized(
                "Ein projektspezifischer Motor."
            ),
            broader_project_concept_ids=(
                "PC-000002",
            ),
            provenance=provenance,
            rationale="Unknown relation target.",
        )


def test_load_project_concept(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    expected = create_candidate(
        repository,
        provenance,
    )

    assert repository.load_project_concept(
        PROJECT_ID,
        "PC-000001",
    ) == expected


@pytest.mark.parametrize(
    "concept_id",
    [
        "PC-000000",
        "PC-1",
        "../PC-000001",
        1,
    ],
)
def test_load_rejects_invalid_concept_id(
    repository: ProjectGlossaryRepository,
    concept_id: object,
) -> None:
    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.load_project_concept(
            PROJECT_ID,
            concept_id,  # type: ignore[arg-type]
        )


def test_load_missing_project_concept(
    repository: ProjectGlossaryRepository,
) -> None:
    with pytest.raises(ProjectConceptNotFoundError):
        repository.load_project_concept(
            PROJECT_ID,
            "PC-000001",
        )


def test_create_candidate_revision_preserves_history(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    original = create_candidate(
        repository,
        provenance,
    )
    revised = repository.create_candidate_revision(
        PROJECT_ID,
        original.project_concept_id,
        definitions=localized(
            "Eine überarbeitete Definition."
        ),
        provenance=provenance,
        rationale="Material definition change.",
    )

    assert revised.project_concept_id == "PC-000001"
    assert revised.latest_revision == 2
    assert revised.revisions[0] == original.revisions[0]
    assert revised.revisions[1].revision == 2
    assert (
        revised.revisions[1].lifecycle_status
        == "candidate"
    )
    assert (
        revised.revisions[1].preferred_labels
        == original.revisions[0].preferred_labels
    )
    assert (
        revised.revisions[1].definitions[0].text
        == "Eine überarbeitete Definition."
    )


def test_candidate_revision_requires_existing_concept(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    with pytest.raises(ProjectConceptNotFoundError):
        repository.create_candidate_revision(
            PROJECT_ID,
            "PC-000001",
            provenance=provenance,
            rationale="Missing concept.",
        )


def test_candidate_revision_requires_provenance(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )

    with pytest.raises(ProjectGlossaryValidationError):
        repository.create_candidate_revision(
            PROJECT_ID,
            concept.project_concept_id,
            provenance=(),
            rationale="Missing evidence.",
        )


def test_stale_update_temporary_file_blocks_mutation(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    glossary_path = repository.glossary_path(PROJECT_ID)
    temporary_path = (
        glossary_path.parent
        / f".{glossary_path.name}.tmp"
    )
    temporary_path.write_text(
        "stale",
        encoding="utf-8",
    )

    with pytest.raises(ProjectGlossaryPersistenceError):
        create_candidate(repository, provenance)

    assert repository.load_glossary(
        PROJECT_ID
    ).glossary_revision == 1


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        ("accept", "accepted"),
        ("reject", "rejected"),
    ],
)
def test_record_candidate_decision(
    repository: ProjectGlossaryRepository,
    provenance,
    decision: str,
    expected_status: str,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    result = repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision=decision,
        reviewer_identity="Moritz Diez",
        rationale="Human terminology review.",
    )

    assert result.terminology_decision_id == "TD-000001"
    assert result.decision == decision
    assert (
        result.resulting_lifecycle_status
        == expected_status
    )
    assert (
        repository.load_project_concept(
            PROJECT_ID,
            concept.project_concept_id,
        ).revisions[0].lifecycle_status
        == expected_status
    )


def test_accept_then_deprecate(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    accepted = repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Meaning accepted.",
    )
    deprecated = repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="deprecate",
        reviewer_identity="Moritz Diez",
        rationale="Meaning superseded.",
    )

    assert (
        accepted.terminology_decision_id
        == "TD-000001"
    )
    assert (
        deprecated.terminology_decision_id
        == "TD-000002"
    )
    assert (
        repository.load_project_concept(
            PROJECT_ID,
            concept.project_concept_id,
        ).revisions[0].lifecycle_status
        == "deprecated"
    )


@pytest.mark.parametrize(
    ("initial_decision", "next_decision"),
    [
        ("accept", "accept"),
        ("reject", "accept"),
        ("reject", "reject"),
        ("reject", "deprecate"),
    ],
)
def test_invalid_lifecycle_transition_is_rejected(
    repository: ProjectGlossaryRepository,
    provenance,
    initial_decision: str,
    next_decision: str,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision=initial_decision,
        reviewer_identity="Moritz Diez",
        rationale="First decision.",
    )

    with pytest.raises(
        InvalidTerminologyLifecycleTransitionError
    ):
        repository.record_terminology_decision(
            PROJECT_ID,
            concept.project_concept_id,
            1,
            decision=next_decision,
            reviewer_identity="Moritz Diez",
            rationale="Invalid second decision.",
        )


@pytest.mark.parametrize(
    "revision_number",
    [
        0,
        True,
        "1",
        2,
    ],
)
def test_decision_requires_existing_positive_revision(
    repository: ProjectGlossaryRepository,
    provenance,
    revision_number: object,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )

    with pytest.raises(
        InvalidTerminologyLifecycleTransitionError
    ):
        repository.record_terminology_decision(
            PROJECT_ID,
            concept.project_concept_id,
            revision_number,  # type: ignore[arg-type]
            decision="accept",
            reviewer_identity="Moritz Diez",
            rationale="Invalid revision.",
        )


def test_decision_ids_are_sequential(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Antrieb",
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Motor",
    )
    first_decision = (
        repository.record_terminology_decision(
            PROJECT_ID,
            first.project_concept_id,
            1,
            decision="accept",
            reviewer_identity="Moritz Diez",
            rationale="First meaning accepted.",
        )
    )
    second_decision = (
        repository.record_terminology_decision(
            PROJECT_ID,
            second.project_concept_id,
            1,
            decision="reject",
            reviewer_identity="Moritz Diez",
            rationale="Second meaning rejected.",
        )
    )

    assert [
        first_decision.terminology_decision_id,
        second_decision.terminology_decision_id,
    ] == [
        "TD-000001",
        "TD-000002",
    ]


def test_decision_is_persisted_before_status_application(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    result = repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Meaning accepted.",
    )

    assert repository.terminology_decision_path(
        PROJECT_ID,
        result.terminology_decision_id,
    ).is_file()
    assert repository.load_terminology_decision(
        PROJECT_ID,
        result.terminology_decision_id,
    ) == result


def test_list_terminology_decisions_is_sorted(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Antrieb",
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Motor",
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        first.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Accepted.",
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        second.project_concept_id,
        1,
        decision="reject",
        reviewer_identity="Moritz Diez",
        rationale="Rejected.",
    )

    assert [
        item.terminology_decision_id
        for item in repository.list_terminology_decisions(
            PROJECT_ID
        )
    ] == [
        "TD-000001",
        "TD-000002",
    ]


def test_load_missing_terminology_decision(
    repository: ProjectGlossaryRepository,
) -> None:
    with pytest.raises(TerminologyDecisionError):
        repository.load_terminology_decision(
            PROJECT_ID,
            "TD-000001",
        )


def test_list_rejects_unexpected_visible_entry(
    repository: ProjectGlossaryRepository,
) -> None:
    (
        repository.terminology_decisions_path(
            PROJECT_ID
        )
        / "unexpected.txt"
    ).write_text(
        "unexpected",
        encoding="utf-8",
    )

    with pytest.raises(TerminologyDecisionError):
        repository.list_terminology_decisions(
            PROJECT_ID
        )


def test_failed_duplicate_preferred_acceptance_publishes_no_decision(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Port",
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="PORT",
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        first.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="First meaning accepted.",
    )

    with pytest.raises(DuplicatePreferredLabelError):
        repository.record_terminology_decision(
            PROJECT_ID,
            second.project_concept_id,
            1,
            decision="accept",
            reviewer_identity="Moritz Diez",
            rationale="Conflicting meaning.",
        )

    assert [
        item.terminology_decision_id
        for item in repository.list_terminology_decisions(
            PROJECT_ID
        )
    ] == ["TD-000001"]


def test_new_revision_can_be_accepted(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Revision one accepted.",
    )
    revised = repository.create_candidate_revision(
        PROJECT_ID,
        concept.project_concept_id,
        definitions=localized(
            "Überarbeitete Definition."
        ),
        provenance=provenance,
        rationale="Material update.",
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        2,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Revision two accepted.",
    )
    loaded = repository.load_project_concept(
        PROJECT_ID,
        concept.project_concept_id,
    )

    assert revised.latest_revision == 2
    assert [
        item.lifecycle_status
        for item in loaded.revisions
    ] == [
        "accepted",
        "accepted",
    ]


def test_create_ambiguity_group_for_candidates(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Physischer Anschluss",
        alternative_labels=localized("Port"),
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Netzwerkendpunkt",
        alternative_labels=localized("PORT"),
    )
    group = repository.create_ambiguity_group(
        PROJECT_ID,
        label="Port",
        language="de",
        candidate_project_concept_ids=(
            first.project_concept_id,
            second.project_concept_id,
        ),
        rationale="Context is required.",
    )

    assert group.ambiguity_group_id == "AG-000001"
    assert group.resolution_rule == "context_required"
    assert group.candidate_project_concept_ids == (
        "PC-000001",
        "PC-000002",
    )


def test_ambiguity_group_allows_both_acceptances(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="Physischer Anschluss",
        alternative_labels=localized("Port"),
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Netzwerkendpunkt",
        alternative_labels=localized("PORT"),
    )
    repository.create_ambiguity_group(
        PROJECT_ID,
        label="Port",
        language="de",
        candidate_project_concept_ids=(
            first.project_concept_id,
            second.project_concept_id,
        ),
        rationale="Context is required.",
    )

    for concept in (first, second):
        repository.record_terminology_decision(
            PROJECT_ID,
            concept.project_concept_id,
            1,
            decision="accept",
            reviewer_identity="Moritz Diez",
            rationale="Meaning accepted.",
        )

    assert repository.scan_project_glossary(
        PROJECT_ID
    ).issues == ()


def test_ambiguity_group_ids_are_sequential(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    labels = (
        (
            "First A",
            "First B",
            "Alpha",
        ),
        (
            "Second A",
            "Second B",
            "Beta",
        ),
    )
    groups = []

    for first_label, second_label, shared in labels:
        first = create_candidate(
            repository,
            provenance,
            preferred_label=first_label,
            alternative_labels=localized(shared),
        )
        second = create_candidate(
            repository,
            provenance,
            preferred_label=second_label,
            alternative_labels=localized(shared),
        )
        groups.append(
            repository.create_ambiguity_group(
                PROJECT_ID,
                label=shared,
                language="de",
                candidate_project_concept_ids=(
                    first.project_concept_id,
                    second.project_concept_id,
                ),
                rationale="Context is required.",
            )
        )

    assert [
        group.ambiguity_group_id
        for group in groups
    ] == [
        "AG-000001",
        "AG-000002",
    ]


def test_ambiguity_group_requires_shared_label(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    first = create_candidate(
        repository,
        provenance,
        preferred_label="First",
    )
    second = create_candidate(
        repository,
        provenance,
        preferred_label="Second",
    )

    with pytest.raises(ProjectGlossaryValidationError):
        repository.create_ambiguity_group(
            PROJECT_ID,
            label="Port",
            language="de",
            candidate_project_concept_ids=(
                first.project_concept_id,
                second.project_concept_id,
            ),
            rationale="Invalid group.",
        )


def test_load_missing_ambiguity_group(
    repository: ProjectGlossaryRepository,
) -> None:
    with pytest.raises(AmbiguityGroupNotFoundError):
        repository.load_ambiguity_group(
            PROJECT_ID,
            "AG-000001",
        )


@pytest.mark.parametrize(
    "group_id",
    [
        "AG-000000",
        "AG-1",
        "../AG-000001",
        1,
    ],
)
def test_load_rejects_invalid_ambiguity_group_id(
    repository: ProjectGlossaryRepository,
    group_id: object,
) -> None:
    with pytest.raises(UnsafeProjectGlossaryPathError):
        repository.load_ambiguity_group(
            PROJECT_ID,
            group_id,  # type: ignore[arg-type]
        )


def test_clean_scan(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Meaning accepted.",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert scan.glossary == repository.load_glossary(
        PROJECT_ID
    )
    assert len(scan.terminology_decisions) == 1
    assert scan.issues == ()


def test_scan_reports_invalid_glossary(
    repository: ProjectGlossaryRepository,
) -> None:
    repository.glossary_path(PROJECT_ID).write_text(
        "{invalid",
        encoding="utf-8",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert scan.glossary is None
    assert [
        issue.code
        for issue in scan.issues
    ] == ["invalid_project_glossary"]


def test_scan_reports_invalid_decision_json(
    repository: ProjectGlossaryRepository,
) -> None:
    path = repository.terminology_decision_path(
        PROJECT_ID,
        "TD-000001",
    )
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert scan.terminology_decisions == ()
    assert [
        issue.code
        for issue in scan.issues
    ] == ["invalid_terminology_decision"]


def test_scan_reports_unexpected_decision_entry(
    repository: ProjectGlossaryRepository,
) -> None:
    path = (
        repository.terminology_decisions_path(
            PROJECT_ID
        )
        / "unexpected.txt"
    )
    path.write_text(
        "unexpected",
        encoding="utf-8",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["invalid_terminology_decision_entry"]


def test_scan_reports_missing_decisions_directory(
    repository: ProjectGlossaryRepository,
) -> None:
    repository.terminology_decisions_path(
        PROJECT_ID
    ).rmdir()

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["missing_terminology_decisions_path"]


def test_scan_reports_decisions_symlink(
    repository: ProjectGlossaryRepository,
    tmp_path: Path,
) -> None:
    path = repository.terminology_decisions_path(
        PROJECT_ID
    )
    path.rmdir()
    outside = tmp_path / "outside-decisions"
    outside.mkdir()
    path.symlink_to(
        outside,
        target_is_directory=True,
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["unsafe_terminology_decisions_path"]


def test_scan_reports_orphan_decision_state(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    decision = create_terminology_decision(
        PROJECT_ID,
        "TD-000001",
        concept.project_concept_id,
        1,
        decision="accept",
        previous_lifecycle_status="candidate",
        reviewer_identity="Moritz Diez",
        decided_at=TIMESTAMP,
        rationale="Published without glossary transition.",
    )
    repository._publish_terminology_decision(
        decision
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["decision_state_mismatch"]


def test_scan_reports_unknown_decision_concept(
    repository: ProjectGlossaryRepository,
) -> None:
    decision = create_terminology_decision(
        PROJECT_ID,
        "TD-000001",
        "PC-000001",
        1,
        decision="accept",
        previous_lifecycle_status="candidate",
        reviewer_identity="Moritz Diez",
        decided_at=TIMESTAMP,
        rationale="Unknown concept.",
    )
    repository._publish_terminology_decision(
        decision
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["unknown_decision_concept"]


def test_scan_reports_unknown_decision_revision(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    decision = create_terminology_decision(
        PROJECT_ID,
        "TD-000001",
        concept.project_concept_id,
        2,
        decision="accept",
        previous_lifecycle_status="candidate",
        reviewer_identity="Moritz Diez",
        decided_at=TIMESTAMP,
        rationale="Unknown revision.",
    )
    repository._publish_terminology_decision(
        decision
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["unknown_decision_revision"]


def test_scan_reports_manual_status_without_decision(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    glossary_path = repository.glossary_path(PROJECT_ID)
    glossary = repository.load_glossary(PROJECT_ID)
    accepted_revision = replace(
        concept.revisions[0],
        lifecycle_status="accepted",
    )
    accepted_concept = replace(
        concept,
        revisions=(accepted_revision,),
    )
    modified = replace(
        glossary,
        concepts=(accepted_concept,),
    )
    glossary_path.write_text(
        project_glossary_to_json(modified),
        encoding="utf-8",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert [
        issue.code
        for issue in scan.issues
    ] == ["decision_state_mismatch"]


def test_hidden_decision_files_are_ignored(
    repository: ProjectGlossaryRepository,
) -> None:
    (
        repository.terminology_decisions_path(
            PROJECT_ID
        )
        / ".temporary"
    ).write_text(
        "ignored operational artifact",
        encoding="utf-8",
    )

    scan = repository.scan_project_glossary(
        PROJECT_ID
    )

    assert scan.issues == ()


def test_project_isolation(
    tmp_path: Path,
    provenance,
) -> None:
    identifiers = iter(
        [
            PROJECT_ID,
            SECOND_PROJECT_ID,
        ]
    )
    projects_root = tmp_path / "projects"
    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: next(identifiers),
        clock=fixed_clock,
    )
    workspace.create_project("First Project")
    workspace.create_project("Second Project")
    repository = ProjectGlossaryRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    repository.initialize_glossary(
        PROJECT_ID,
        default_language="de",
    )
    repository.initialize_glossary(
        SECOND_PROJECT_ID,
        default_language="en",
    )
    first = repository.create_candidate_concept(
        PROJECT_ID,
        preferred_labels=localized("Antrieb"),
        definitions=localized("Definition"),
        provenance=provenance,
        rationale="First project concept.",
    )

    assert first.project_concept_id == "PC-000001"
    assert len(
        repository.load_glossary(
            PROJECT_ID
        ).concepts
    ) == 1
    assert repository.load_glossary(
        SECOND_PROJECT_ID
    ).concepts == ()

    with pytest.raises(ProjectConceptNotFoundError):
        repository.load_project_concept(
            SECOND_PROJECT_ID,
            "PC-000001",
        )


def test_persisted_decision_contains_no_engineering_approval(
    repository: ProjectGlossaryRepository,
    provenance,
) -> None:
    concept = create_candidate(
        repository,
        provenance,
    )
    decision = repository.record_terminology_decision(
        PROJECT_ID,
        concept.project_concept_id,
        1,
        decision="accept",
        reviewer_identity="Moritz Diez",
        rationale="Terminology accepted.",
    )
    payload = json.loads(
        repository.terminology_decision_path(
            PROJECT_ID,
            decision.terminology_decision_id,
        ).read_text(encoding="utf-8")
    )

    assert "engineering_approval" not in payload
    assert "approved_information_unit_id" not in payload