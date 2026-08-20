"""Contract tests for the Derivation Assessment task prompt."""

from modules.ingestion.agent_tasks import (
    get_derivation_assessor_task_instructions,
)


def _prompt() -> str:
    return get_derivation_assessor_task_instructions(
        "DERIVATION_RULE_SENTINEL"
    )


def test_derivation_prompt_uses_candidate_ids_for_relationship_endpoints():
    prompt = _prompt()
    assert '"source_element_candidate": "ELEM_001"' in prompt
    assert '"target_element_candidate": "ELEM_002"' in prompt
    assert "candidate name or candidate ID" not in prompt
    assert "Relationship endpoints MUST use candidate IDs only." in prompt


def test_derivation_prompt_requires_closed_relationship_endpoint_set():
    prompt = _prompt()
    assert (
        "Every source_element_candidate and target_element_candidate MUST "
        "reference"
    ) in prompt
    normalized_prompt = " ".join(prompt.split())
    assert (
        "first create a source-supported candidate element for that entity"
        in normalized_prompt
    )


def test_derivation_prompt_keeps_explicit_entity_when_classification_uncertain():
    prompt = _prompt()
    assert (
        "Do not omit an explicit entity merely because its precise downstream "
        "SysML"
    ) in prompt
    assert "least-assumptive allowed element_type" in prompt
    assert "missing_information" in prompt


def test_derivation_prompt_contains_compact_domain_neutral_examples():
    prompt = _prompt()
    assert "The technician operates the calibration station." in prompt
    assert "The controller shall store the measurement result." in prompt
    assert "Do NOT invent a database" in prompt


def test_derivation_prompt_contains_output_self_check():
    prompt = _prompt()
    assert "perform this self-check" in prompt
    assert "Every enum value exactly matches" in prompt
    assert "No JSON object contains duplicate keys." in prompt
    assert "Every relationship has explicit or direct source evidence." in prompt


def test_derivation_prompt_preserves_exact_enum_contract_and_rules():
    prompt = _prompt()
    assert "states_constraint" in prompt
    assert "describes_constraint" not in prompt
    assert "physical_element" not in prompt
    assert "DERIVATION_RULE_SENTINEL" in prompt


def test_derivation_prompt_removes_contradictory_relationship_instruction():
    prompt = _prompt()
    assert "Do not propose relationships." not in prompt
    assert "Do not invent relationships" in prompt
