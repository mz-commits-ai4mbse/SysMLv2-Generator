"""R4c.3c prompt contract tests."""

from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)
from modules.subject_interpretation import (
    build_subject_interpretation_task_instructions,
)


def test_prompt_forbids_persona_rediscovery_and_sysml_modeling():
    value = build_subject_interpretation_task_instructions()

    assert "Do NOT detect new subjects." in value
    assert "Do NOT merge, split or rename subjects." in value
    assert "Interpret EACH supplied SUBJ-* exactly once." in value
    assert "Do NOT perform SysML v2 model derivation." in value


def test_prompt_reuses_existing_semantic_dimensions():
    value = build_subject_interpretation_task_instructions()

    assert "Do NOT return `semantic_kind`." in value
    assert "Use ONLY the existing ADR-011 classification dimensions." in value

    for choice in INFORMATION_TYPES:
        assert choice in value
    for choice in STATEMENT_MODALITIES:
        assert choice in value
    for choice in EPISTEMIC_CLASSES:
        if choice != "derivation":
            assert choice in value


def test_prompt_keeps_relationships_pre_model_and_explicit():
    value = build_subject_interpretation_task_instructions()

    assert "PRE-MODEL RELATIONSHIP HINTS" in value
    assert "source_subject_id" in value
    assert "target_subject_id" in value
    assert "are not ontology relations" in value
    assert "are not SysML relationships" in value


def test_prompt_removes_persona_supplied_confidence():
    value = build_subject_interpretation_task_instructions()

    assert "Do not output an LLM confidence score." in value
    assert '"confidence"' not in value
