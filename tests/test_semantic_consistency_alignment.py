import json

import pytest

from modules.llm.types import LLMResult
from modules.semantic_consistency_alignment import (
    SemanticConsistencyAlignmentService,
    SemanticConsistencyAlignmentValidationError,
    find_semantic_consistency_needs,
    pair_is_consistent,
    semantic_consistency_result_to_json,
)


class Client:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return LLMResult(
            text=json.dumps(self.output),
            provider=request.provider,
            model=request.model,
            response_id="consistency-1",
        )


def raw(epistemic="explicit", missing=None):
    return json.dumps(
        {
            "interpretations": [
                {
                    "canonical_subject_id": "SUBJ-000001",
                    "interpreted_statement": "A source-grounded statement.",
                    "information_type": "constraint",
                    "statement_modality": "descriptive",
                    "epistemic_class": epistemic,
                    "missing_evidence": missing,
                    "rationale": "Source-grounded.",
                    "uncertainties": [],
                }
            ],
            "relationships": [],
        }
    )


def align(client, text):
    return SemanticConsistencyAlignmentService(
        client_factory=lambda provider: client
    ).align_output(
        text,
        item_id_field="canonical_subject_id",
        allowed_item_ids=("SUBJ-000001",),
        context_by_item_id={
            "SUBJ-000001": "Source context."
        },
        provider="openai",
        model="gpt-test",
    )


@pytest.mark.parametrize(
    ("epistemic", "missing"),
    (
        ("explicit", None),
        ("interpretation", None),
        ("assumption", "A required fact is not present."),
    ),
)
def test_consistent_pair_needs_no_mapper(epistemic, missing):
    client = Client()
    result = align(client, raw(epistemic, missing))
    assert result.decisions == ()
    assert result.normalized_output_text == raw(epistemic, missing)
    assert client.requests == []


def test_object_missing_evidence_is_detected_without_content_specific_rule():
    needs = find_semantic_consistency_needs(
        raw(
            "explicit",
            {"reason": "commentary", "details": "not evidence"},
        ),
        item_id_field="canonical_subject_id",
        allowed_item_ids=("SUBJ-000001",),
    )
    assert len(needs) == 1
    assert needs[0].raw_epistemic_class == "explicit"
    assert isinstance(needs[0].raw_missing_evidence, dict)


def test_mapper_can_resolve_commentary_to_explicit_null():
    client = Client(
        {
            "resolutions": [
                {
                    "item_id": "SUBJ-000001",
                    "normalized_epistemic_class": "explicit",
                    "normalized_missing_evidence": None,
                    "rationale": (
                        "The non-null content is commentary rather than "
                        "a genuine evidence gap."
                    ),
                }
            ]
        }
    )
    result = align(
        client,
        raw("explicit", {"reason": "commentary"}),
    )
    payload = json.loads(result.normalized_output_text)
    item = payload["interpretations"][0]
    assert item["epistemic_class"] == "explicit"
    assert item["missing_evidence"] is None
    assert len(client.requests) == 1


def test_mapper_can_preserve_real_gap_as_assumption_text():
    client = Client(
        {
            "resolutions": [
                {
                    "item_id": "SUBJ-000001",
                    "normalized_epistemic_class": "assumption",
                    "normalized_missing_evidence": (
                        "The source does not identify the controlling actor."
                    ),
                    "rationale": "The raw content describes a genuine evidence gap.",
                }
            ]
        }
    )
    result = align(
        client,
        raw(
            "explicit",
            {
                "reason": "Actor not identified",
                "details": "Control responsibility is unstated.",
            },
        ),
    )
    payload = json.loads(result.normalized_output_text)
    item = payload["interpretations"][0]
    assert item["epistemic_class"] == "assumption"
    assert item["missing_evidence"] == (
        "The source does not identify the controlling actor."
    )


def test_invalid_mapper_pair_fails_closed():
    client = Client(
        {
            "resolutions": [
                {
                    "item_id": "SUBJ-000001",
                    "normalized_epistemic_class": "explicit",
                    "normalized_missing_evidence": "still non-null",
                    "rationale": "invalid pair",
                }
            ]
        }
    )
    with pytest.raises(SemanticConsistencyAlignmentValidationError):
        align(client, raw("explicit", {"reason": "commentary"}))


def test_provider_failure_has_no_lossy_fallback():
    client = Client(error=RuntimeError("provider down"))
    with pytest.raises(RuntimeError, match="provider down"):
        align(client, raw("explicit", {"reason": "commentary"}))


def test_serialization_preserves_raw_and_normalized_pair():
    client = Client(
        {
            "resolutions": [
                {
                    "item_id": "SUBJ-000001",
                    "normalized_epistemic_class": "explicit",
                    "normalized_missing_evidence": None,
                    "rationale": "Commentary is not missing evidence.",
                }
            ]
        }
    )
    result = align(
        client,
        raw("explicit", {"reason": "commentary"}),
    )
    payload = json.loads(
        semantic_consistency_result_to_json(result)
    )
    decision = payload["decisions"][0]
    assert decision["raw_epistemic_class"] == "explicit"
    assert decision["raw_missing_evidence"] == {"reason": "commentary"}
    assert decision["normalized_epistemic_class"] == "explicit"
    assert decision["normalized_missing_evidence"] is None
    assert len(decision["content_fingerprint"]) == 64


def test_pair_invariant():
    assert pair_is_consistent("explicit", None)
    assert pair_is_consistent("interpretation", None)
    assert pair_is_consistent("assumption", "gap")
    assert not pair_is_consistent("explicit", "gap")
    assert not pair_is_consistent("assumption", None)
