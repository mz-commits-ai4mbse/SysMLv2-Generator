"""R4c.2c prompt guard for independently meaningful canonical Subjects."""

from modules.engineering_subjects.prompt import (
    ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION,
    build_engineering_subject_discovery_instructions,
)


def test_discovery_prompt_requires_subject_self_sufficiency():
    prompt = build_engineering_subject_discovery_instructions()

    assert ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION == "1.3.1"
    assert "SELF-SUFFICIENCY PASS" in prompt
    assert "independently referable" in prompt
    assert "dependent clause" in prompt
    assert "fragment whose meaning is incomplete" in prompt
    assert "Do not create a separate canonical Subject" in prompt


def test_self_sufficiency_rule_is_generic_not_domain_hardcoded():
    prompt = build_engineering_subject_discovery_instructions().lower()

    assert "acceptable" not in prompt
    assert "connection-quality" not in prompt
    assert "microscope" not in prompt
