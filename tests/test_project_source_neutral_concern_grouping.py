"""Focused tests for ADR-034 source-neutral concern grouping."""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_reconciliation.case_persistence import (
    semantic_index_from_json,
    semantic_index_to_json,
)
from modules.project_semantic_reconciliation.case_contract import (
    create_project_semantic_index_artifact,
)
from modules.project_semantic_reconciliation.case_types import (
    PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION,
    SemanticIndexGroupProposal,
)
from modules.project_semantic_reconciliation.semantic_index_prompt import (
    build_project_semantic_index_instructions,
)


@dataclass(frozen=True)
class Subject:
    subject_ref: str
    source_id: str


def same_source_subjects():
    return (
        Subject(
            "project_subject:SRC-000003:SP-000003:CSUB-000001",
            "SRC-000003",
        ),
        Subject(
            "project_subject:SRC-000003:SP-000003:CSUB-000002",
            "SRC-000003",
        ),
        Subject(
            "project_subject:SRC-000003:SP-000003:CSUB-000003",
            "SRC-000003",
        ),
    )


def test_same_source_multi_member_group_is_valid_non_singleton_case():
    subjects = same_source_subjects()

    index = create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=subjects,
        group_proposals=(
            SemanticIndexGroupProposal(
                group_label="Remote control requirements",
                member_subject_refs=tuple(
                    subject.subject_ref for subject in subjects
                ),
            ),
        ),
        llm_provider="openai",
        llm_model="gpt-test",
        llm_response_id="resp-s3a-1",
        llm_output_fingerprint="b" * 64,
    )

    assert len(index.cases) == 1
    case = index.cases[0]
    assert case.singleton is False
    assert case.source_ids == ("SRC-000003",)
    assert case.member_subject_refs == tuple(
        sorted(subject.subject_ref for subject in subjects)
    )
    assert index.human_review_required is True


def test_same_source_multi_member_case_roundtrips_persistence():
    subjects = same_source_subjects()

    index = create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=subjects,
        group_proposals=(
            SemanticIndexGroupProposal(
                "Remote control requirements",
                tuple(subject.subject_ref for subject in subjects),
            ),
        ),
        llm_provider="openai",
        llm_model="gpt-test",
        llm_response_id="resp-s3a-1",
        llm_output_fingerprint="b" * 64,
    )

    assert (
        index.schema_version
        == PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION
    )
    assert semantic_index_from_json(
        semantic_index_to_json(index)
    ) == index


def test_unique_semantics_depend_on_subject_count_not_source_count():
    subjects = same_source_subjects()

    index = create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=subjects,
        group_proposals=tuple(
            SemanticIndexGroupProposal(
                group_label=f"Concern {position}",
                member_subject_refs=(subject.subject_ref,),
            )
            for position, subject in enumerate(subjects, start=1)
        ),
        llm_provider="openai",
        llm_model="gpt-test",
        llm_response_id="resp-s3a-2",
        llm_output_fingerprint="c" * 64,
    )

    assert len(index.cases) == 3
    assert all(case.singleton for case in index.cases)
    assert all(case.source_ids == ("SRC-000003",) for case in index.cases)
    assert index.human_review_required is False


def test_prompt_declares_source_id_provenance_only():
    instructions = build_project_semantic_index_instructions().lower()

    assert "source_id is provenance only" in instructions
    assert "must not constrain" in instructions
    assert "same source" in instructions
