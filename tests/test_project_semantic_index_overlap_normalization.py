"""Focused I2D.5D4.3 overlap-normalized concern grouping tests."""

from __future__ import annotations

import pytest

from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
)
from modules.project_semantic_reconciliation.semantic_index_prompt import (
    PROJECT_SEMANTIC_INDEX_PROMPT_SCHEMA_VERSION,
    build_project_semantic_index_instructions,
)
from modules.project_semantic_reconciliation.semantic_index_service import (
    parse_project_semantic_index_response,
)


def parse(text: str, refs=("SUBJ-0001", "SUBJ-0002", "SUBJ-0003")):
    return parse_project_semantic_index_response(
        text,
        transport_subject_refs=refs,
    )


def test_direct_overlap_is_normalized_into_one_final_group():
    proposals = parse(
        '''{
          "groups": [
            {
              "group_label": "Remote control",
              "member_subject_refs": ["SUBJ-0001", "SUBJ-0002"]
            },
            {
              "group_label": "Purpose of collaboration",
              "member_subject_refs": ["SUBJ-0002", "SUBJ-0003"]
            }
          ]
        }'''
    )

    assert len(proposals) == 1
    assert proposals[0].member_subject_refs == (
        "SUBJ-0001",
        "SUBJ-0002",
        "SUBJ-0003",
    )
    assert proposals[0].group_label == (
        "Purpose of collaboration / Remote control"
    )


def test_transitive_overlap_forms_one_connected_component():
    proposals = parse(
        '''{
          "groups": [
            {
              "group_label": "A",
              "member_subject_refs": ["SUBJ-0001"]
            },
            {
              "group_label": "B",
              "member_subject_refs": ["SUBJ-0001", "SUBJ-0002"]
            },
            {
              "group_label": "C",
              "member_subject_refs": ["SUBJ-0002", "SUBJ-0003"]
            }
          ]
        }'''
    )

    assert len(proposals) == 1
    assert proposals[0].group_label == "A / B / C"
    assert proposals[0].member_subject_refs == (
        "SUBJ-0001",
        "SUBJ-0002",
        "SUBJ-0003",
    )


def test_disjoint_groups_remain_separate_and_deterministic():
    proposals = parse(
        '''{
          "groups": [
            {
              "group_label": "Audio",
              "member_subject_refs": ["SUBJ-0003"]
            },
            {
              "group_label": "Remote control",
              "member_subject_refs": ["SUBJ-0002", "SUBJ-0001"]
            }
          ]
        }'''
    )

    assert tuple(
        item.member_subject_refs for item in proposals
    ) == (
        ("SUBJ-0001", "SUBJ-0002"),
        ("SUBJ-0003",),
    )
    assert tuple(item.group_label for item in proposals) == (
        "Remote control",
        "Audio",
    )


def test_missing_subject_still_fails_closed_after_overlap_normalization():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="missing:.*SUBJ-0003",
    ):
        parse(
            '''{
              "groups": [
                {
                  "group_label": "A",
                  "member_subject_refs": ["SUBJ-0001", "SUBJ-0002"]
                },
                {
                  "group_label": "B",
                  "member_subject_refs": ["SUBJ-0002"]
                }
              ]
            }'''
        )


def test_duplicate_inside_one_raw_group_still_fails_closed():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="duplicate Subject refs",
    ):
        parse(
            '''{
              "groups": [
                {
                  "group_label": "A",
                  "member_subject_refs": [
                    "SUBJ-0001",
                    "SUBJ-0001",
                    "SUBJ-0002",
                    "SUBJ-0003"
                  ]
                }
              ]
            }'''
        )


def test_prompt_contract_explicitly_allows_bounded_overlap_proposals():
    instructions = build_project_semantic_index_instructions().lower()

    assert PROJECT_SEMANTIC_INDEX_PROMPT_SCHEMA_VERSION == "1.1.0"
    assert "at least once" in instructions
    assert "may appear in more than one proposed group" in instructions
    assert "overlapping" in instructions
    assert "final case" in instructions
