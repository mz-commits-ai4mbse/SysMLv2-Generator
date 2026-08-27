import json

import pytest

from modules.classification_alignment import (
    ClassificationAlignmentService,
    ClassificationAlignmentValidationError,
    build_classification_alignment_instructions,
)
from modules.llm.types import LLMResult


class Client:
    def __init__(self, outputs=(), error=None):
        self.outputs = list(outputs)
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return LLMResult(
            text=json.dumps(self.outputs.pop(0)),
            provider=request.provider,
            model=request.model,
            response_id=f"align-{len(self.requests)}",
        )


def raw(value, field="information_type"):
    item = {
        "canonical_subject_id": "SUBJ-000001",
        "interpreted_statement": "The source describes a semantic concept.",
        "information_type": "requirement",
        "statement_modality": "descriptive",
        "epistemic_class": "explicit",
        "missing_evidence": None,
        "rationale": "Source-grounded.",
        "uncertainties": [],
    }
    item[field] = value
    return json.dumps({"interpretations": [item], "relationships": []})


def align(client, text):
    return ClassificationAlignmentService(
        client_factory=lambda provider: client
    ).align_output(
        text,
        item_id_field="canonical_subject_id",
        allowed_item_ids={"SUBJ-000001"},
        context_by_item_id={"SUBJ-000001": "Relevant source-grounded context."},
        provider="openai",
        model="gpt-test",
    )


def mapper(target, status="mapped"):
    return {
        "alignments": [
            {
                "item_id": "SUBJ-000001",
                "field_name": "information_type",
                "normalized_value": target,
                "mapping_status": status,
                "rationale": "Context supports this controlled representation.",
            }
        ]
    }


def test_valid_controlled_value_needs_no_mapper_call():
    client = Client()
    result = align(client, raw("requirement"))
    assert result.decisions == ()
    assert client.requests == []


def test_lexical_normalization_needs_no_mapper_call():
    client = Client()
    result = align(client, raw(" Requirement "))
    assert json.loads(result.normalized_output_text)["interpretations"][0]["information_type"] == "requirement"
    assert result.decisions[0].mapping_status == "lexical"
    assert client.requests == []


@pytest.mark.parametrize(("source_term", "target"), (("architecture", "logical_element"), ("condition", "constraint")))
def test_contextual_mapper_can_translate_raw_semantic_expression(source_term, target):
    client = Client((mapper(target),))
    result = align(client, raw(source_term))
    item = json.loads(result.normalized_output_text)["interpretations"][0]
    assert item["information_type"] == target
    assert result.decisions[0].raw_value == source_term
    assert result.decisions[0].mapping_status == "mapped"
    assert len(client.requests) == 1


def test_ambiguous_information_type_becomes_unclassified():
    client = Client((mapper("unclassified", "ambiguous"),))
    result = align(client, raw("architecture"))
    assert json.loads(result.normalized_output_text)["interpretations"][0]["information_type"] == "unclassified"
    assert result.decisions[0].mapping_status == "ambiguous"


def test_invalid_mapper_target_cannot_enter_pipeline():
    client = Client((mapper("condition"),))
    result = align(client, raw("condition"))
    assert json.loads(result.normalized_output_text)["interpretations"][0]["information_type"] == "unclassified"
    assert result.decisions[0].mapping_status == "fallback_unclassified"


def test_provider_failure_degrades_only_information_type_to_unclassified():
    result = align(Client(error=RuntimeError("offline")), raw("architecture"))
    assert json.loads(result.normalized_output_text)["interpretations"][0]["information_type"] == "unclassified"
    assert result.decisions[0].mapping_status == "fallback_unclassified"


def test_field_without_neutral_value_remains_fail_closed():
    client = Client(({
        "alignments": [{
            "item_id": "SUBJ-000001",
            "field_name": "statement_modality",
            "normalized_value": "casual",
            "mapping_status": "mapped",
            "rationale": "Still invalid.",
        }]
    },))
    with pytest.raises(ClassificationAlignmentValidationError):
        align(client, raw("assertive", "statement_modality"))


def test_prompt_is_generic_and_keeps_ontology_mapping_downstream():
    prompt = build_classification_alignment_instructions()
    assert "CONTROLLED CLASSIFICATION ALIGNMENT" in prompt
    assert "BFO" in prompt and "IOF" in prompt
    assert "microscope" not in prompt.lower()
    assert "workstation" not in prompt.lower()

def test_alignment_result_serialization_is_auditable():
    from modules.classification_alignment import (
        classification_alignment_result_to_json,
    )

    client = Client((mapper("logical_element"),))
    result = align(client, raw("architecture"))

    payload = json.loads(
        classification_alignment_result_to_json(result)
    )

    assert payload["schema_version"] == "1.0.0"
    assert payload["mapper_response_id"] == "align-1"
    assert len(payload["decisions"]) == 1

    decision = payload["decisions"][0]
    assert decision["item_id"] == "SUBJ-000001"
    assert decision["field_name"] == "information_type"
    assert decision["raw_value"] == "architecture"
    assert decision["normalized_value"] == "logical_element"
    assert decision["mapping_status"] == "mapped"
    assert decision["mapper_response_id"] == "align-1"
    assert len(decision["content_fingerprint"]) == 64
