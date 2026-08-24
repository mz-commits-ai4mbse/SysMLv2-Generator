"""R4c Subject Interpretation prompt version contract."""

from modules.subject_interpretation.prompt import (
    SUBJECT_INTERPRETATION_PROMPT_SCHEMA_VERSION,
)


def test_subject_interpretation_prompt_schema_version():
    assert SUBJECT_INTERPRETATION_PROMPT_SCHEMA_VERSION == "1.4.0"
