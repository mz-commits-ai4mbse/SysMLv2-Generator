"""Focused tests for ADR-033 I2D.5C Case assessment + summary."""

from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace

import pytest

import modules.project_semantic_reconciliation.case_service as module
from modules.project_semantic_reconciliation.case_contract import (
    create_project_semantic_index_artifact,
)
from modules.project_semantic_reconciliation.case_service import (
    ProjectReconciliationCaseAssessmentService,
    parse_project_reconciliation_case_response,
)
from modules.project_semantic_reconciliation.case_types import (
    SemanticIndexGroupProposal,
)
from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
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
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        output = self.outputs[len(self.requests) - 1]
        return SimpleNamespace(
            text=json.dumps(output),
            provider=request.provider,
            model=request.model,
            response_id=f"case-{len(self.requests)}",
        )


def subjects():
    return (
        EvidenceSubject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
            "SP-000001",
            "CSUB-000001",
            "Viewer limit",
        ),
        EvidenceSubject(
            "project_subject:SRC-000002:SP-000002:CSUB-000004",
            "SRC-000002",
            "SP-000002",
            "CSUB-000004",
            "Viewer limit",
        ),
        EvidenceSubject(
            "project_subject:SRC-000003:SP-000003:CSUB-000002",
            "SRC-000003",
            "SP-000003",
            "CSUB-000002",
            "Audio channel",
        ),
    )


def index():
    values = subjects()
    return create_project_semantic_index_artifact(
        project_id="308131",
        input_fingerprint="a" * 64,
        subjects=values,
        group_proposals=(
            SemanticIndexGroupProposal(
                "Concurrent viewers",
                (values[0].subject_ref, values[1].subject_ref),
            ),
            SemanticIndexGroupProposal(
                "Audio channel",
                (values[2].subject_ref,),
            ),
        ),
    )


def complementary_output():
    return {
        "shared_concern": "Concurrent viewers",
        "outcome": "complementary",
        "summary": "Compatible statements at different detail levels.",
        "shared_concepts": ["viewer count"],
        "material_differences": ["different abstraction"],
        "claim_groups": [],
    }


def test_one_llm_call_per_non_singleton_case_only():
    semantic_index = index()
    client = Client([complementary_output()])

    assessments, summary = ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
    )

    assert len(client.requests) == 1
    assert len(assessments) == 2
    assert {assessment.outcome for assessment in assessments} == {
        "complementary",
        "unique",
    }
    assert summary.case_count == 2


def test_singleton_is_unique_without_llm_call():
    semantic_index = index()
    client = Client([complementary_output()])

    assessments, _ = ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
    )

    unique = next(
        assessment
        for assessment in assessments
        if assessment.outcome == "unique"
    )
    assert unique.llm_provider is None
    assert unique.llm_model is None
    assert unique.llm_response_id is None
    assert unique.human_review_required is False


def test_case_call_sees_only_case_local_transient_refs():
    semantic_index = index()
    client = Client([complementary_output()])

    ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
    )

    payload = json.loads(client.requests[0].input_text)
    assert [
        subject["subject_ref"]
        for subject in payload["subjects"]
    ] == ["SUBJ-0001", "SUBJ-0002"]
    assert "project_subject:" not in client.requests[0].input_text


def test_case_task_is_not_pairwise():
    instructions = module.build_project_reconciliation_case_instructions()

    assert "AS A WHOLE" in instructions
    assert "do not return pairwise relations" in instructions
    assert "Never choose which Source is correct" in instructions


def test_potential_conflict_restores_real_refs_in_claim_groups():
    semantic_index = index()
    client = Client(
        [
            {
                "shared_concern": "Maximum concurrent viewers",
                "outcome": "potential_conflict",
                "summary": "Sources specify incompatible maxima.",
                "shared_concepts": ["viewer limit"],
                "material_differences": ["2 versus 5"],
                "claim_groups": [
                    {
                        "summary": "maximum = 2",
                        "supported_by_subject_refs": ["SUBJ-0001"],
                    },
                    {
                        "summary": "maximum = 5",
                        "supported_by_subject_refs": ["SUBJ-0002"],
                    },
                ],
            }
        ]
    )

    assessments, summary = ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
    )

    conflict = next(
        assessment
        for assessment in assessments
        if assessment.outcome == "potential_conflict"
    )
    real = {subject.subject_ref for subject in subjects()[:2]}
    assert {
        ref
        for group in conflict.claim_groups
        for ref in group.supported_by_subject_refs
    } == real
    assert summary.potential_conflicts_present is True


def test_conflict_claim_groups_must_partition_every_case_subject():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="partition every Case Subject",
    ):
        parse_project_reconciliation_case_response(
            json.dumps(
                {
                    "shared_concern": "Viewer limit",
                    "outcome": "potential_conflict",
                    "summary": "Conflict.",
                    "shared_concepts": ["viewer limit"],
                    "material_differences": ["2 vs 5"],
                    "claim_groups": [
                        {
                            "summary": "2",
                            "supported_by_subject_refs": ["SUBJ-0001"],
                        }
                    ],
                }
            ),
            transport_subject_refs=("SUBJ-0001", "SUBJ-0002"),
        )


def test_unknown_claim_group_ref_fails_closed():
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="unknown subject_ref",
    ):
        parse_project_reconciliation_case_response(
            json.dumps(
                {
                    "shared_concern": "Viewer limit",
                    "outcome": "potential_conflict",
                    "summary": "Conflict.",
                    "shared_concepts": ["viewer limit"],
                    "material_differences": ["2 vs 5"],
                    "claim_groups": [
                        {
                            "summary": "2",
                            "supported_by_subject_refs": ["SUBJ-0001"],
                        },
                        {
                            "summary": "5",
                            "supported_by_subject_refs": ["SUBJ-9999"],
                        },
                    ],
                }
            ),
            transport_subject_refs=("SUBJ-0001", "SUBJ-0002"),
        )


def test_s3b_subject_set_must_exactly_match_s3a_index():
    semantic_index = index()
    client = Client([complementary_output()])

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="exact S3A semantic index",
    ):
        ProjectReconciliationCaseAssessmentService(
            client_factory=lambda provider: client
        ).assess_all(
            semantic_index=semantic_index,
            subjects=subjects()[:2],
            provider="openai",
            model="gpt-test",
        )

    assert client.requests == []


def test_summary_is_derived_without_extra_llm_call():
    semantic_index = index()
    client = Client([complementary_output()])

    _, summary = ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
    )

    assert len(client.requests) == 1
    assert summary.potential_conflicts_present is False
    assert summary.uncertainties_present is False
    assert dict(summary.outcome_counts) == {
        "complementary": 1,
        "unique": 1,
    }


def test_case_progress_includes_singletons_but_llm_count_does_not():
    semantic_index = index()
    client = Client([complementary_output()])
    events = []

    ProjectReconciliationCaseAssessmentService(
        client_factory=lambda provider: client
    ).assess_all(
        semantic_index=semantic_index,
        subjects=subjects(),
        provider="openai",
        model="gpt-test",
        case_progress_observer=events.append,
    )

    assert len(events) == 4
    assert [event.event_type for event in events] == [
        "started",
        "completed",
        "started",
        "completed",
    ]
    assert {event.singleton for event in events} == {False, True}


def test_bounded_case_input_fails_before_llm_call(monkeypatch):
    semantic_index = index()
    client = Client([complementary_output()])
    monkeypatch.setattr(
        module,
        "PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS",
        10,
    )

    with pytest.raises(
        ProjectSemanticReconciliationValidationError,
        match="bounded contract",
    ):
        ProjectReconciliationCaseAssessmentService(
            client_factory=lambda provider: client
        ).assess_all(
            semantic_index=semantic_index,
            subjects=subjects(),
            provider="openai",
            model="gpt-test",
        )

    assert client.requests == []
