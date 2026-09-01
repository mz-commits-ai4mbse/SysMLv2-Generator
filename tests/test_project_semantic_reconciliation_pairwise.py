from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace

import pytest

import modules.project_semantic_reconciliation.service as module


@dataclass(frozen=True)
class FakeSubject:
    subject_ref: str
    source_id: str
    source_projection_id: str
    canonical_subject_id: str


@dataclass(frozen=True)
class FakeRelation:
    left_subject_ref: str
    right_subject_ref: str
    outcome: str = "equivalent"
    rationale: str = "same meaning"
    shared_concepts: tuple[str, ...] = ("shared",)
    material_differences: tuple[str, ...] = ()


class PairClient:
    def __init__(self, fail_on_call=None):
        self.calls = []
        self.fail_on_call = fail_on_call

    def generate(self, request):
        self.calls.append(request)
        call_index = len(self.calls)

        if self.fail_on_call == call_index:
            raise RuntimeError(f"pair call {call_index} failed")

        payload = json.loads(request.input_text)
        subjects = payload["subjects"]

        return SimpleNamespace(
            text=json.dumps(
                {
                    "relations": [],
                    "unmatched_subject_refs": [
                        subject["subject_ref"]
                        for subject in subjects
                    ],
                }
            ),
            provider=request.provider,
            model=request.model,
            response_id=f"pair-response-{call_index}",
        )


def subjects_for_sources(*source_ids):
    result = []
    for index, source_id in enumerate(source_ids, start=1):
        result.append(
            FakeSubject(
                subject_ref=(
                    f"project_subject:{source_id}:"
                    f"SP-{index:06d}:CSUB-{index:06d}"
                ),
                source_id=source_id,
                source_projection_id=f"SP-{index:06d}",
                canonical_subject_id=f"CSUB-{index:06d}",
            )
        )
    return tuple(result)


def install_lightweight_contract(monkeypatch, subjects, captured):
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda source_inputs: (
            "308131",
            subjects,
            "f" * 64,
        ),
    )

    def build_input(*, project_id, subjects):
        return json.dumps(
            {
                "project_id": project_id,
                "subjects": [
                    {
                        "subject_ref": subject.subject_ref,
                        "source_id": subject.source_id,
                    }
                    for subject in subjects
                ],
            }
        )

    monkeypatch.setattr(
        module,
        "build_project_semantic_reconciliation_input",
        build_input,
    )

    def parse(text, *, subjects):
        payload = json.loads(text)
        known = {subject.subject_ref for subject in subjects}

        unmatched = tuple(payload["unmatched_subject_refs"])
        if set(unmatched) != known and payload["relations"] == []:
            raise module.ProjectSemanticReconciliationIntegrityError(
                "pair coverage invalid"
            )

        relations = tuple(
            FakeRelation(
                left_subject_ref=item["left_subject_ref"],
                right_subject_ref=item["right_subject_ref"],
            )
            for item in payload["relations"]
        )
        return relations, unmatched

    monkeypatch.setattr(
        module,
        "parse_project_semantic_reconciliation_response",
        parse,
    )

    def create_artifact(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(
        module,
        "create_project_semantic_reconciliation_artifact",
        create_artifact,
    )


def service(client):
    return module.ProjectSemanticReconciliationService(
        client_factory=lambda provider: client
    )


def test_two_sources_create_exactly_one_singular_pair(monkeypatch):
    subjects = subjects_for_sources("SRC-000001", "SRC-000002")
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)
    client = PairClient()

    service(client).reconcile(
        (object(), object()),
        provider="openai",
        model="gpt-test",
    )

    assert len(client.calls) == 1
    metadata = client.calls[0].metadata
    assert metadata["source_pair_index"] == 1
    assert metadata["source_pair_count"] == 1
    assert metadata["left_source_id"] == "SRC-000001"
    assert metadata["right_source_id"] == "SRC-000002"
    assert captured["llm_response_id"] == "pair-response-1"


def test_four_sources_create_six_pairs_in_deterministic_order(
    monkeypatch,
):
    subjects = subjects_for_sources(
        "SRC-000004",
        "SRC-000002",
        "SRC-000001",
        "SRC-000003",
    )
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)
    client = PairClient()

    service(client).reconcile(
        (object(),) * 4,
        provider="openai",
        model="gpt-test",
    )

    pairs = [
        (
            request.metadata["left_source_id"],
            request.metadata["right_source_id"],
        )
        for request in client.calls
    ]
    assert pairs == [
        ("SRC-000001", "SRC-000002"),
        ("SRC-000001", "SRC-000003"),
        ("SRC-000001", "SRC-000004"),
        ("SRC-000002", "SRC-000003"),
        ("SRC-000002", "SRC-000004"),
        ("SRC-000003", "SRC-000004"),
    ]
    assert captured["llm_response_id"] is None
    assert captured["input_fingerprint"] == "f" * 64


def test_pair_alias_space_is_local_to_each_call(monkeypatch):
    subjects = subjects_for_sources(
        "SRC-000001",
        "SRC-000002",
        "SRC-000003",
    )
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)
    client = PairClient()

    service(client).reconcile(
        (object(),) * 3,
        provider="openai",
        model="gpt-test",
    )

    for request in client.calls:
        refs = [
            item["subject_ref"]
            for item in json.loads(request.input_text)["subjects"]
        ]
        assert refs == ["SUBJ-0001", "SUBJ-0002"]


def test_global_unmatched_requires_no_relation_in_any_pair(monkeypatch):
    subjects = subjects_for_sources(
        "SRC-000001",
        "SRC-000002",
        "SRC-000003",
    )
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)

    class RelatingClient(PairClient):
        def generate(self, request):
            self.calls.append(request)
            payload = json.loads(request.input_text)
            pair = (
                request.metadata["left_source_id"],
                request.metadata["right_source_id"],
            )
            refs = [item["subject_ref"] for item in payload["subjects"]]

            if pair == ("SRC-000001", "SRC-000002"):
                body = {
                    "relations": [
                        {
                            "left_subject_ref": refs[0],
                            "right_subject_ref": refs[1],
                        }
                    ],
                    "unmatched_subject_refs": [],
                }
            else:
                body = {
                    "relations": [],
                    "unmatched_subject_refs": refs,
                }

            return SimpleNamespace(
                text=json.dumps(body),
                provider=request.provider,
                model=request.model,
                response_id=f"pair-response-{len(self.calls)}",
            )

    def parse_with_relations(text, *, subjects):
        payload = json.loads(text)
        relations = tuple(
            FakeRelation(
                left_subject_ref=item["left_subject_ref"],
                right_subject_ref=item["right_subject_ref"],
            )
            for item in payload["relations"]
        )
        return relations, tuple(payload["unmatched_subject_refs"])

    monkeypatch.setattr(
        module,
        "parse_project_semantic_reconciliation_response",
        parse_with_relations,
    )

    service(RelatingClient()).reconcile(
        (object(),) * 3,
        provider="openai",
        model="gpt-test",
    )

    assert set(captured["unmatched_subject_refs"]) == {
        subjects[2].subject_ref,
    }
    assert {
        captured["relations"][0].left_subject_ref,
        captured["relations"][0].right_subject_ref,
    } == {
        subjects[0].subject_ref,
        subjects[1].subject_ref,
    }


def test_one_failed_pair_aborts_whole_s3_before_artifact(monkeypatch):
    subjects = subjects_for_sources(
        "SRC-000001",
        "SRC-000002",
        "SRC-000003",
        "SRC-000004",
    )
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)
    client = PairClient(fail_on_call=3)
    events = []

    with pytest.raises(RuntimeError, match="pair call 3 failed"):
        service(client).reconcile(
            (object(),) * 4,
            provider="openai",
            model="gpt-test",
            pair_progress_observer=events.append,
        )

    assert len(client.calls) == 3
    assert captured == {}
    assert events[-1].event_type == "failed"
    assert events[-1].pair_index == 3
    assert events[-1].total_pairs == 6


def test_pair_progress_reports_real_six_pair_sequence(monkeypatch):
    subjects = subjects_for_sources(
        "SRC-000001",
        "SRC-000002",
        "SRC-000003",
        "SRC-000004",
    )
    captured = {}
    install_lightweight_contract(monkeypatch, subjects, captured)
    events = []

    service(PairClient()).reconcile(
        (object(),) * 4,
        provider="openai",
        model="gpt-test",
        pair_progress_observer=events.append,
    )

    assert len(events) == 12
    completed = [
        event
        for event in events
        if event.event_type == "completed"
    ]
    assert [event.pair_index for event in completed] == [
        1, 2, 3, 4, 5, 6
    ]


def test_pair_prompt_is_explicitly_singular():
    assert "exactly two registered Engineering Sources" in (
        module._PROJECT_SEMANTIC_PAIR_INSTRUCTIONS
    )
    assert "performs only the bounded semantic comparison" in (
        module._PROJECT_SEMANTIC_PAIR_INSTRUCTIONS
    )
