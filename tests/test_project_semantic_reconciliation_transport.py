from __future__ import annotations

from dataclasses import dataclass
import json

import pytest

from modules.project_semantic_reconciliation import (
    ProjectSemanticReconciliationIntegrityError,
    parse_project_semantic_reconciliation_response,
)

from modules.project_semantic_reconciliation.service import (
    _PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS,
    _prepare_project_semantic_transport_subjects,
    _restore_project_semantic_subject_refs,
)


@dataclass(frozen=True)
class FakeSubject:
    subject_ref: str
    source_id: str


@dataclass(frozen=True)
class FakeRelation:
    left_subject_ref: str
    right_subject_ref: str
    outcome: str = "equivalent"


def test_transport_aliases_are_deterministic_and_transient():
    subjects = (
        FakeSubject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
        ),
        FakeSubject(
            "project_subject:SRC-000002:SP-000002:CSUB-000007",
            "SRC-000002",
        ),
    )

    transport, mapping = _prepare_project_semantic_transport_subjects(
        subjects
    )

    assert tuple(item.subject_ref for item in transport) == (
        "SUBJ-0001",
        "SUBJ-0002",
    )
    assert mapping == {
        "SUBJ-0001": subjects[0].subject_ref,
        "SUBJ-0002": subjects[1].subject_ref,
    }


def test_transport_round_trip_restores_exact_project_subject_refs():
    mapping = {
        "SUBJ-0001": (
            "project_subject:SRC-000001:SP-000001:CSUB-000001"
        ),
        "SUBJ-0002": (
            "project_subject:SRC-000002:SP-000002:CSUB-000007"
        ),
    }
    relations, unmatched = _restore_project_semantic_subject_refs(
        (
            FakeRelation(
                left_subject_ref="SUBJ-0001",
                right_subject_ref="SUBJ-0002",
            ),
        ),
        (),
        transport_to_subject_ref=mapping,
    )

    assert relations[0].left_subject_ref == mapping["SUBJ-0001"]
    assert relations[0].right_subject_ref == mapping["SUBJ-0002"]
    assert unmatched == ()


def test_unknown_transport_alias_fails_closed_without_fuzzy_recovery():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="unknown transient subject_ref",
    ):
        _restore_project_semantic_subject_refs(
            (
                FakeRelation(
                    left_subject_ref="SUBJ-0001",
                    right_subject_ref="SUBJ-9999",
                ),
            ),
            (),
            transport_to_subject_ref={
                "SUBJ-0001": (
                    "project_subject:SRC-000001:SP-000001:CSUB-000001"
                ),
                "SUBJ-0002": (
                    "project_subject:SRC-000002:SP-000002:CSUB-000007"
                ),
            },
        )


def test_duplicate_project_subject_identity_fails_before_transport():
    duplicate = (
        FakeSubject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
        ),
        FakeSubject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
        ),
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="not unique",
    ):
        _prepare_project_semantic_transport_subjects(duplicate)


def test_same_source_transport_relation_remains_forbidden():
    subjects = (
        FakeSubject("SUBJ-0001", "SRC-000001"),
        FakeSubject("SUBJ-0002", "SRC-000001"),
    )
    response = json.dumps(
        {
            "relations": [
                {
                    "left_subject_ref": "SUBJ-0001",
                    "right_subject_ref": "SUBJ-0002",
                    "outcome": "equivalent",
                    "rationale": "same concern",
                    "shared_concepts": ["concern"],
                    "material_differences": [],
                }
            ],
            "unmatched_subject_refs": [],
        }
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="different Sources",
    ):
        parse_project_semantic_reconciliation_response(
            response,
            subjects=subjects,
        )


def test_complete_subject_coverage_remains_mandatory_with_aliases():
    subjects = (
        FakeSubject("SUBJ-0001", "SRC-000001"),
        FakeSubject("SUBJ-0002", "SRC-000002"),
    )
    response = json.dumps(
        {
            "relations": [],
            "unmatched_subject_refs": ["SUBJ-0001"],
        }
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="explicitly cover every Subject",
    ):
        parse_project_semantic_reconciliation_response(
            response,
            subjects=subjects,
        )


def test_transport_instructions_forbid_identifier_reconstruction():
    assert "opaque transport identifiers" in (
        _PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS
    )
    assert "SUBJ-NNNN" in _PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS
    assert "Never construct, infer, shorten, expand, normalize" in (
        _PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS
    )
