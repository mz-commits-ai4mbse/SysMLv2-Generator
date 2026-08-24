"""R4c.5b.4 relationship decision persistence tests."""

import pytest

from modules.project_workspace import ProjectWorkspace
from modules.subject_review.relationship_decisions import (
    SubjectRelationshipDecisionRepository,
    create_subject_relationship_decision_record,
    subject_relationship_decision_from_json,
    subject_relationship_decision_to_json,
)


def _record(**changes):
    values = dict(
        project_id="396272",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000003",
        decision_id="SRD-000001",
        predecessor_decision_id=None,
        subject_review_card_fingerprint="a" * 64,
        source_subject_id="SUBJ-000002",
        relationship_kind="uses",
        target_subject_id="SUBJ-000006",
        outcome="accepted",
        rationale=None,
        reviewer_identity="reviewer",
        created_at="2026-08-24T06:30:00Z",
    )
    values.update(changes)
    return create_subject_relationship_decision_record(**values)


def test_record_round_trip_and_reject_guard():
    value = _record()
    assert subject_relationship_decision_from_json(
        subject_relationship_decision_to_json(value)
    ) == value

    with pytest.raises(ValueError):
        _record(outcome="rejected", rationale=None)


def test_repository_is_append_only_and_tracks_successor(tmp_path):
    workspace = ProjectWorkspace(
        root=tmp_path,
        id_generator=lambda: "396272",
    )
    assert workspace.create_project("Test Project").project_id == "396272"

    repository = SubjectRelationshipDecisionRepository(root=tmp_path)
    first = _record(outcome="deferred")
    repository.append(first)

    second = _record(
        decision_id="SRD-000002",
        predecessor_decision_id="SRD-000001",
        outcome="accepted",
    )
    repository.append(second)

    assert repository.list_decisions(
        "396272",
        "RVD-000001",
        "RVV-000001",
    ) == (first, second)
    assert repository.latest_by_relationship(
        "396272",
        "RVD-000001",
        "RVV-000001",
    ) == (second,)
