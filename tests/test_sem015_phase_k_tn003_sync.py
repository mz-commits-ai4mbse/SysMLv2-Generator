from modules.sysml_validation.relationship_validator import (
    _ELEMENT,
    _KEYWORD_TO_CONSTRUCT,
)
from modules.sysml_validation.target_notation_validator import (
    _ELEMENT_HEADER,
)


def test_k2_accepts_tn003_part_definition_header():
    match = _ELEMENT_HEADER.fullmatch("part def IME_000001 {")
    assert match is not None
    assert match.group(1) == "part def"
    assert match.group(2) == "IME_000001"


def test_k3_resolves_tn003_part_definition_header():
    match = _ELEMENT.fullmatch("part def IME_000001 {")
    assert match is not None
    assert match.group(1) == "part def"
    assert match.group(2) == "IME_000001"
    assert _KEYWORD_TO_CONSTRUCT[match.group(1)] == "TN_003"


def test_existing_part_usage_mapping_is_unchanged():
    match = _ELEMENT.fullmatch("part IME_000004 {")
    assert match is not None
    assert _KEYWORD_TO_CONSTRUCT[match.group(1)] == "TN_004"
