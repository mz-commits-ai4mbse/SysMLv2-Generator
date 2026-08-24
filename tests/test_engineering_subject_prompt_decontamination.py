"""Guard the production discovery prompt against benchmark leakage."""

from pathlib import Path


def test_subject_discovery_prompt_is_not_wp12_example_specific():
    text = Path(
        "modules/engineering_subjects/prompt.py"
    ).read_text(encoding="utf-8").lower()

    assert "remote expert" not in text
    assert "the expert" not in text
