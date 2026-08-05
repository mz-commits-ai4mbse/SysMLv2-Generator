"""Tests for exact persisted P4 evidence references."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from modules.framework_assignment import (
    framework_assignment_candidate_to_json,
)
from modules.human_review import (
    human_review_decision_to_json,
)
from modules.information_units import (
    information_unit_to_json,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.p4_evidence_adapter import (
    P4ReviewEvidenceRecord,
    P4ReviewEvidenceSet,
)
from modules.review_workspace.p4_evidence_reference_adapter import (
    P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE,
    P4_HUMAN_REVIEW_EVIDENCE_ROLE,
    P4_INFORMATION_UNIT_EVIDENCE_ROLE,
    P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE,
    construct_p4_evidence_references,
)
from modules.terminology_mapping import (
    terminology_mapping_candidate_to_json,
)

from tests.test_review_workspace_p4_evidence_adapter import (
    OTHER_PROJECT_ID,
    OTHER_SOURCE_ID,
    PROJECT_ID,
    SOURCE_ID,
    _decision,
    _framework_candidate,
    _information_unit,
    _terminology_candidate,
)


def _record(
    *,
    information_unit=None,
    terminology_candidates=(),
    framework_candidates=(),
    decisions=(),
) -> P4ReviewEvidenceRecord:
    selected_information_unit = (
        _information_unit()
        if information_unit is None
        else information_unit
    )

    return P4ReviewEvidenceRecord(
        information_unit=selected_information_unit,
        terminology_mapping_candidates=tuple(
            terminology_candidates
        ),
        framework_assignment_candidates=tuple(
            framework_candidates
        ),
        human_review_decisions=tuple(decisions),
    )


def _evidence_set(
    records,
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
) -> P4ReviewEvidenceSet:
    return P4ReviewEvidenceSet(
        project_id=project_id,
        source_id=source_id,
        records=tuple(records),
    )


def _artifact_path(
    repository_root: Path,
    *,
    directory: str,
    artifact_id: str,
) -> Path:
    return (
        repository_root
        / "data"
        / "projects"
        / PROJECT_ID
        / "semantics"
        / directory
        / f"{artifact_id}.json"
    )


def _write_text(
    target: Path,
    text: str,
) -> None:
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    target.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )


def _persist_record(
    repository_root: Path,
    record: P4ReviewEvidenceRecord,
) -> None:
    information_unit = record.information_unit

    _write_text(
        _artifact_path(
            repository_root,
            directory="information_units",
            artifact_id=(
                information_unit.information_unit_id
            ),
        ),
        information_unit_to_json(
            information_unit
        ),
    )

    for candidate in (
        record.terminology_mapping_candidates
    ):
        _write_text(
            _artifact_path(
                repository_root,
                directory="terminology_mappings",
                artifact_id=(
                    candidate
                    .terminology_mapping_candidate_id
                ),
            ),
            terminology_mapping_candidate_to_json(
                candidate
            ),
        )

    for candidate in (
        record.framework_assignment_candidates
    ):
        _write_text(
            _artifact_path(
                repository_root,
                directory="framework_assignments",
                artifact_id=(
                    candidate
                    .framework_assignment_candidate_id
                ),
            ),
            framework_assignment_candidate_to_json(
                candidate
            ),
        )

    for decision in record.human_review_decisions:
        _write_text(
            _artifact_path(
                repository_root,
                directory="human_reviews",
                artifact_id=(
                    decision.human_review_decision_id
                ),
            ),
            human_review_decision_to_json(decision),
        )


def _complete_record() -> P4ReviewEvidenceRecord:
    information_unit = _information_unit()
    terminology = _terminology_candidate(
        information_unit
    )
    framework = _framework_candidate(
        information_unit,
        terminology,
    )

    decisions = (
        _decision(
            decision_id="HRD-000001",
            target_type=(
                "information_unit_publication"
            ),
            target_id=(
                information_unit.information_unit_id
            ),
            content_fingerprint=(
                information_unit.content_fingerprint
            ),
        ),
        _decision(
            decision_id="HRD-000002",
            target_type=(
                "terminology_mapping_candidate"
            ),
            target_id=(
                terminology
                .terminology_mapping_candidate_id
            ),
            content_fingerprint=(
                terminology.content_fingerprint
            ),
        ),
        _decision(
            decision_id="HRD-000003",
            target_type=(
                "framework_assignment_candidate"
            ),
            target_id=(
                framework
                .framework_assignment_candidate_id
            ),
            content_fingerprint=(
                framework.content_fingerprint
            ),
        ),
    )

    return _record(
        information_unit=information_unit,
        terminology_candidates=(terminology,),
        framework_candidates=(framework,),
        decisions=decisions,
    )


def test_binds_complete_p4_record_to_persisted_files(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _complete_record()
    _persist_record(repository_root, record)

    selected = construct_p4_evidence_references(
        _evidence_set((record,)),
        repository_root=repository_root,
    )

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert len(selected.records) == 1

    bound = selected.records[0]

    assert (
        bound.information_unit_id
        == record.information_unit
        .information_unit_id
    )
    assert len(
        bound.all_evidence_references
    ) == 6

    roles = tuple(
        reference.evidence_role
        for reference
        in bound.all_evidence_references
    )

    assert roles == (
        P4_INFORMATION_UNIT_EVIDENCE_ROLE,
        P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE,
        P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE,
        P4_HUMAN_REVIEW_EVIDENCE_ROLE,
        P4_HUMAN_REVIEW_EVIDENCE_ROLE,
        P4_HUMAN_REVIEW_EVIDENCE_ROLE,
    )

    for reference in (
        bound.all_evidence_references
    ):
        artifact = reference.artifact_reference
        target = (
            repository_root
            / artifact.repository_relative_path
        )

        assert (
            artifact.content_fingerprint
            == hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
        )
        assert reference.evidence_locator == "/"


def test_uses_professional_p4_fingerprints(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _complete_record()
    _persist_record(repository_root, record)

    selected = construct_p4_evidence_references(
        _evidence_set((record,)),
        repository_root=repository_root,
    )
    bound = selected.records[0]

    assert (
        bound.information_unit_reference
        .evidence_content_fingerprint
        == record.information_unit
        .content_fingerprint
    )

    assert (
        bound.terminology_mapping_references[0]
        .evidence_content_fingerprint
        == record.terminology_mapping_candidates[0]
        .content_fingerprint
    )

    assert (
        bound.framework_assignment_references[0]
        .evidence_content_fingerprint
        == record.framework_assignment_candidates[0]
        .content_fingerprint
    )

    assert {
        reference.evidence_content_fingerprint
        for reference
        in bound.human_review_references
    } == {
        decision.decision_fingerprint
        for decision in record.human_review_decisions
    }


def test_record_order_is_deterministic(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first = _record(
        information_unit=_information_unit(
            information_unit_id="IU-000001",
        )
    )
    second = _record(
        information_unit=_information_unit(
            information_unit_id="IU-000002",
            statement=(
                "The pump shall preserve "
                "model traceability."
            ),
        )
    )

    _persist_record(repository_root, first)
    _persist_record(repository_root, second)

    forward = construct_p4_evidence_references(
        _evidence_set((first, second)),
        repository_root=repository_root,
    )
    reverse = construct_p4_evidence_references(
        _evidence_set((second, first)),
        repository_root=repository_root,
    )

    assert forward == reverse

    assert tuple(
        record.information_unit_id
        for record in forward.records
    ) == (
        "IU-000001",
        "IU-000002",
    )


def test_empty_p4_set_remains_empty(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    selected = construct_p4_evidence_references(
        _evidence_set(()),
        repository_root=repository_root,
    )

    assert selected.records == ()


def test_rejects_missing_persisted_artifact(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()

    with pytest.raises(
        ReviewReferenceError,
        match="does not exist",
    ):
        construct_p4_evidence_references(
            _evidence_set((record,)),
            repository_root=repository_root,
        )


def test_rejects_noncanonical_persisted_artifact(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()
    _persist_record(repository_root, record)

    target = _artifact_path(
        repository_root,
        directory="information_units",
        artifact_id=(
            record.information_unit
            .information_unit_id
        ),
    )
    target.write_text(
        target.read_text(encoding="utf-8")
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="canonical value",
    ):
        construct_p4_evidence_references(
            _evidence_set((record,)),
            repository_root=repository_root,
        )


def test_rejects_symbolic_link_artifact(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()
    _persist_record(repository_root, record)

    target = _artifact_path(
        repository_root,
        directory="information_units",
        artifact_id=(
            record.information_unit
            .information_unit_id
        ),
    )
    outside = tmp_path / "outside.json"
    outside.write_text(
        information_unit_to_json(
            record.information_unit
        ),
        encoding="utf-8",
    )

    target.unlink()

    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip(
            "Symbolic links are unavailable "
            "on this platform."
        )

    with pytest.raises(
        ReviewReferenceError,
        match="symbolic links",
    ):
        construct_p4_evidence_references(
            _evidence_set((record,)),
            repository_root=repository_root,
        )


def test_rejects_cross_project_record(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Project",
    ):
        construct_p4_evidence_references(
            _evidence_set(
                (record,),
                project_id=OTHER_PROJECT_ID,
            ),
            repository_root=repository_root,
        )


def test_rejects_cross_source_record(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Source",
    ):
        construct_p4_evidence_references(
            _evidence_set(
                (record,),
                source_id=OTHER_SOURCE_ID,
            ),
            repository_root=repository_root,
        )


def test_rejects_duplicate_information_unit_records(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _record()
    _persist_record(repository_root, record)

    with pytest.raises(
        ReviewIntegrityError,
        match="unique Information Unit",
    ):
        construct_p4_evidence_references(
            _evidence_set((record, record)),
            repository_root=repository_root,
        )


def test_rejects_nonexistent_repository_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ReviewReferenceError,
        match="existing directory",
    ):
        construct_p4_evidence_references(
            _evidence_set(()),
            repository_root=(
                tmp_path / "missing-repository"
            ),
        )


def test_information_unit_lookup_is_fail_closed(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    selected = construct_p4_evidence_references(
        _evidence_set(()),
        repository_root=repository_root,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="No P4 evidence references",
    ):
        selected.evidence_for_information_unit(
            "IU-000999"
        )
