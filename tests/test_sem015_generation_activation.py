from modules.sysml_generation.element_renderer import SysMLElementRenderer
from modules.sysml_generation.generation_profile import (
    load_generation_profile,
)


def test_stakeholder_mapping_is_explicitly_tn003_supported():
    profile = load_generation_profile()
    mapping = next(
        item
        for item in profile["element_mappings"]
        if item["rule_id"] == "J2_ELEMENT_001"
    )
    assert mapping["element_type"] == "stakeholder"
    assert mapping["mapping_status"] == "supported"
    assert mapping["target_construct_id"] == "TN_003"
    assert mapping["target_element_kind"] == "definition"
    assert mapping["production_generation_allowed"] is True


def test_tn003_has_deterministic_part_definition_renderer():
    assert SysMLElementRenderer._KEYWORDS["TN_003"] == "part def"
