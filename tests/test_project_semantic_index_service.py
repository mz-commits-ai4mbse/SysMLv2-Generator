"""Focused tests for ADR-033 I2D.5B global semantic indexing."""

from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace

import pytest

import modules.project_semantic_reconciliation.semantic_index_service as module
from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from modules.project_semantic_reconciliation.semantic_index_service import (
    ProjectSemanticIndexService,
    parse_project_semantic_index_response,
)


@dataclass(frozen=True)
class EvidenceSubject:
    subject_ref: str
    source_id: str
    source_projection_id: str
    canonical_subject_id: str
    canonical_label: str
    subject_form: str = "requirement"
    identity_status: str = "stable"
    source_review_attention_required: bool = False
    mention_evidence: tuple = ()
    statement_evidence: tuple = ()
    field_evidence: tuple = ()


class Client:
    def __init__(self, groups):
        self.groups = groups
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return SimpleNamespace(
            text=json.dumps({"groups": self.groups}),
            provider=request.provider,
            model=request.model,
            response_id="semantic-index-1",
        )


def real_subjects():
    return (
        EvidenceSubject(
            subject_ref=(
                "project_subject:SRC-000001:SP-000001:CSUB-000001"
            ),
            source_id="SRC-000001",
            source_projection_id="SP-000001",
            canonical_subject_id="CSUB-000001",
            canonical_label="Remote client",
        ),
        EvidenceSubject(
            subject_ref=(
                "project_subject:SRC-000002:SP-000002:CSUB-000004"
            ),
            source_id="SRC-000002",
            source_projection_id="SP-000002",
            canonical_subject_id="CSUB-000004",
            canonical_label="Remote consumer",
        ),
        EvidenceSubject(
            subject_ref=(
                "project_subject:SRC-000003:SP-000003:CSUB-000002"
            ),
            source_id="SRC-000003",
            source_projection_id="SP-000003",
            canonical_subject_id="CSUB-000002",
            canonical_label="Audio channel",
        ),
    )


def install_subjects(monkeypatch):
    subjects = real_subjects()
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda source_inputs: ("308131", subjects, "a" * 64),
    )
    return subjects


def test_s3a_is_one_global_llm_call(monkeypatch):
    install_subjects(monkeypatch)
    client = Client(
        [
            {
                "group_label": "Remote client",
                "member_subject_refs": ["SUBJ-0001", "SUBJ-0002"],
            },
            {
                "group_label": "Audio channel",
                "member_subject_refs": ["SUBJ-0003"],
            },
        ]
    )

    artifact = ProjectSemanticIndexService(
        client_factory=lambda provider: client
    ).index(
        (object(), object(), object()),
        provider="openai",
        model="gpt-test",
    )

    assert len(client.requests) == 1
    assert client.requests[0].metadata["task_name"] == (
        "project_semantic_index"
    )
    assert client.requests[0].metadata["source_count"] == 3
    assert client.requests[0].metadata["subject_count"] == 3
    assert len(artifact.cases) == 2


def test_llm_sees_only_transient_subject_refs(monkeypatch):
    install_subjects(monkeypatch)
    client = Client(
        [
            {
                "group_label": "one",
                "member_subject_refs": ["SUBJ-0001"],
            },
            {
                "group_label": "two",
                "member_subject_refs": ["SUBJ-0002"],
            },
            {
                "group_label": "three",
                "member_subject_refs": ["SUBJ-0003"],
            },
        ]
    )

    ProjectSemanticIndexService(
        client_factory=lambda provider: client
    ).index(
        (object(),) * 3,
        provider="openai",
        model="gpt-test",
    )

    payload = json.loads(client.requests[0].input_text)
    assert [
        item["subject_ref"]
        for item in payload["subjects"]
    ] == ["SUBJ-0001", "SUBJ-0002", "SUBJ-0003"]
    assert "project_subject:" not in client.requests[0].input_text


def test_real_project_subject_identity_is_restored_before_case_creation(
    monkeypatch,
):
    subjects = install_subjects(monkeypatch)
    client = Client(
        [
            {
                "group_label": "Remote client",
                "member_subject_refs": ["SUBJ-0002", "SUBJ-0001"],
            },
            {
                "group_label": "Audio",
                "member_subject_refs": ["SUBJ-0003"],
            },
        ]
    )

    artifact = ProjectSemanticIndexService(
        client_factory=lambda provider: client
    ).index(
        (object(),) * 3,
        provider="openai",
        model="gpt-test",
    )

    remote_case = next(
        case for case in artifact.cases if not case.singleton
    )
    assert remote_case.member_subject_refs == tuple(
        sorted(
            (
                subjects[0].subject_ref,
                subjects[1].subject_ref,
            )
        )
    )


def test_unknown_transport_ref_fails_closed():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="unknown subject_ref",
    ):
        parse_project_semantic_index_response(
            json.dumps(
                {
                    "groups": [
                        {
                            "group_label": "bad",
                            "member_subject_refs": ["SUBJ-9999"],
                        }
                    ]
                }
            ),
            transport_subject_refs=("SUBJ-0001",),
        )


def test_duplicate_assignment_across_groups_is_overlap_normalized():
    proposals = parse_project_semantic_index_response(
        json.dumps(
            {
                "groups": [
                    {
                        "group_label": "one",
                        "member_subject_refs": ["SUBJ-0001"],
                    },
                    {
                        "group_label": "two",
                        "member_subject_refs": [
                            "SUBJ-0001",
                            "SUBJ-0002",
                        ],
                    },
                ]
            }
        ),
        transport_subject_refs=("SUBJ-0001", "SUBJ-0002"),
    )

    assert len(proposals) == 1
    assert proposals[0].member_subject_refs == (
        "SUBJ-0001",
        "SUBJ-0002",
    )
    assert proposals[0].group_label == "one / two"


def test_missing_subject_fails_closed():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="cover every Subject",
    ):
        parse_project_semantic_index_response(
            json.dumps(
                {
                    "groups": [
                        {
                            "group_label": "one",
                            "member_subject_refs": ["SUBJ-0001"],
                        }
                    ]
                }
            ),
            transport_subject_refs=("SUBJ-0001", "SUBJ-0002"),
        )


def test_empty_group_is_invalid():
    with pytest.raises(
        ProjectSemanticReconciliationValidationError,
        match="non-empty JSON array",
    ):
        parse_project_semantic_index_response(
            json.dumps(
                {
                    "groups": [
                        {
                            "group_label": "empty",
                            "member_subject_refs": [],
                        }
                    ]
                }
            ),
            transport_subject_refs=("SUBJ-0001",),
        )


def test_s3a_does_not_ask_for_conflict_or_authority(monkeypatch):
    install_subjects(monkeypatch)
    client = Client(
        [
            {
                "group_label": "one",
                "member_subject_refs": ["SUBJ-0001"],
            },
            {
                "group_label": "two",
                "member_subject_refs": ["SUBJ-0002"],
            },
            {
                "group_label": "three",
                "member_subject_refs": ["SUBJ-0003"],
            },
        ]
    )

    ProjectSemanticIndexService(
        client_factory=lambda provider: client
    ).index(
        (object(),) * 3,
        provider="openai",
        model="gpt-test",
    )

    instructions = client.requests[0].instructions
    assert "SEMANTIC INDEXING ONLY" in instructions
    assert "Do not decide whether grouped statements agree or conflict" in (
        instructions
    )
    assert "do not create Engineering Authority" in instructions


def test_bounded_input_failure_occurs_before_llm_call(monkeypatch):
    install_subjects(monkeypatch)
    client = Client([])
    monkeypatch.setattr(
        module,
        "PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS",
        10,
    )

    with pytest.raises(
        ProjectSemanticReconciliationValidationError,
        match="bounded contract",
    ):
        ProjectSemanticIndexService(
            client_factory=lambda provider: client
        ).index(
            (object(),) * 3,
            provider="openai",
            model="gpt-test",
        )

    assert client.requests == []
