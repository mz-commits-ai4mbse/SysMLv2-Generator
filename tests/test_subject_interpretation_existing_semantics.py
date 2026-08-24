"""R4c.3c tests for semantic-reference stage boundaries."""

from modules.subject_interpretation import (
    APOLLO_STRUCTURE_REFERENCE_PATH,
    TURING_CORE_PATH,
    build_subject_interpretation_input,
    build_subject_interpretation_task_instructions,
    existing_downstream_reference_paths,
)


def test_existing_references_remain_linked_downstream():
    paths = existing_downstream_reference_paths()

    assert TURING_CORE_PATH in paths
    assert APOLLO_STRUCTURE_REFERENCE_PATH in paths


def test_prompt_does_not_load_ontology_or_example_reference_content():
    value = build_subject_interpretation_task_instructions()

    assert "Do NOT perform Turing Core concept mapping." in value
    assert "Do NOT perform BFO or IOF ontology mapping." in value
    assert "Do NOT use Apollo 11 as classification input." in value
    assert "Do NOT return `semantic_kind`." in value


def test_prompt_enforces_existing_information_type_vocabulary():
    value = build_subject_interpretation_task_instructions()

    assert "Use ONLY the existing ADR-011 classification dimensions." in value
    assert "Never manufacture a new information_type" in value
    assert "unclassified" in value
