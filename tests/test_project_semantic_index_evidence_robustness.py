"""Focused I2D.5D3 S3A provenance and incomplete-response tests."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

import modules.project_semantic_reconciliation.semantic_index_service as service_module
from modules.llm.openai_client import get_incomplete_reason
from modules.llm.types import LLMResult
from modules.project_reconciliation.case_persistence import (
    semantic_index_from_json,
    semantic_index_to_json,
)
from modules.project_semantic_reconciliation.case_contract import (
    create_project_semantic_index_artifact,
)
from modules.project_semantic_reconciliation.case_types import (
    PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION,
    PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION,
    SemanticIndexGroupProposal,
)
from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
)
from modules.project_semantic_reconciliation.semantic_index_service import (
    ProjectSemanticIndexService,
)


@dataclass(frozen=True)
class Subject:
    subject_ref: str
    source_id: str
    source_projection_id: str
    canonical_subject_id: str
    canonical_label: str
    subject_form: str = "entity"
    identity_status: str = "stable"
    source_review_attention_required: bool = False
    mention_evidence: tuple = ()
    statement_evidence: tuple = ()
    field_evidence: tuple = ()


class Client:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.result


def subjects():
    return (
        Subject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
            "SP-000001",
            "CSUB-000001",
            "Remote client",
        ),
        Subject(
            "project_subject:SRC-000002:SP-000002:CSUB-000002",
            "SRC-000002",
            "SP-000002",
            "CSUB-000002",
            "Remote client",
        ),
    )


def patch_subject_preparation(monkeypatch):
    value = subjects()
    monkeypatch.setattr(
        service_module,
        "prepare_project_semantic_subjects",
        lambda source_inputs: ("308131", value, "a" * 64),
    )
    return value


def test_incomplete_response_fails_before_coverage_parser(monkeypatch):
    patch_subject_preparation(monkeypatch)
    client = Client(
        LLMResult(
            text='{"groups":[]}',
            provider="openai",
            model="gpt-test",
            response_id="resp-incomplete",
            raw_status="incomplete",
            incomplete_reason="max_output_tokens",
        )
    )
    service = ProjectSemanticIndexService(
        client_factory=lambda provider: client
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="incomplete.*max_output_tokens",
    ):
        service.index(
            (),
            provider="openai",
            model="gpt-test",
        )


def test_completed_but_missing_subject_remains_coverage_failure(monkeypatch):
    patch_subject_preparation(monkeypatch)
    client = Client(
        LLMResult(
            text=json.dumps(
                {
                    "groups": [
                        {
                            "group_label": "Remote client",
                            "member_subject_refs": ["SUBJ-0001"],
                        }
                    ]
                }
            ),
            provider="openai",
            model="gpt-test",
            response_id="resp-omission",
            raw_status="completed",
        )
    )
    service = ProjectSemanticIndexService(
        client_factory=lambda provider: client
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="missing:.*SUBJ-0002",
    ):
        service.index(
            (),
            provider="openai",
            model="gpt-test",
        )


def test_completed_s3a_binds_provider_model_response_and_output(monkeypatch):
    source_subjects = patch_subject_preparation(monkeypatch)
    output = json.dumps(
        {
            "groups": [
                {
                    "group_label": "Remote client",
                    "member_subject_refs": [
                        "SUBJ-0001",
                        "SUBJ-0002",
                    ],
                }
            ]
        },
        separators=(",", ":"),
    )
    client = Client(
        LLMResult(
            text=output,
            provider="openai",
            model="gpt-test",
            response_id="resp-index-1",
            raw_status="completed",
        )
    )
    service = ProjectSemanticIndexService(
        client_factory=lambda provider: client
    )

    artifact = service.index(
        (),
        provider="openai",
        model="gpt-test",
    )

    assert artifact.schema_version == (
        PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION
    )
    assert artifact.llm_provider == "openai"
    assert artifact.llm_model == "gpt-test"
    assert artifact.llm_response_id == "resp-index-1"
    assert artifact.llm_output_fingerprint == sha256(
        output.encode("utf-8")
    ).hexdigest()
    assert set(artifact.subject_refs) == {
        item.subject_ref for item in source_subjects
    }


def test_legacy_semantic_index_1_0_remains_roundtrip_readable():
    source_subjects = subjects()
    artifact = create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=source_subjects,
        group_proposals=(
            SemanticIndexGroupProposal(
                "Remote client",
                tuple(item.subject_ref for item in source_subjects),
            ),
        ),
    )

    assert artifact.schema_version == PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION
    text = semantic_index_to_json(artifact)
    assert "llm_provider" not in text
    assert semantic_index_from_json(text) == artifact


def test_semantic_index_1_1_roundtrips_exact_provenance():
    source_subjects = subjects()
    artifact = create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=source_subjects,
        group_proposals=(
            SemanticIndexGroupProposal(
                "Remote client",
                tuple(item.subject_ref for item in source_subjects),
            ),
        ),
        llm_provider="openai",
        llm_model="gpt-test",
        llm_response_id="resp-index-1",
        llm_output_fingerprint="b" * 64,
    )

    text = semantic_index_to_json(artifact)
    loaded = semantic_index_from_json(text)

    assert loaded == artifact
    assert loaded.schema_version == (
        PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION
    )
    assert loaded.llm_output_fingerprint == "b" * 64


def test_openai_incomplete_reason_extraction_supports_object_and_dict():
    assert get_incomplete_reason(
        SimpleNamespace(
            incomplete_details=SimpleNamespace(
                reason="max_output_tokens"
            )
        )
    ) == "max_output_tokens"

    assert get_incomplete_reason(
        SimpleNamespace(
            incomplete_details={"reason": "content_filter"}
        )
    ) == "content_filter"
