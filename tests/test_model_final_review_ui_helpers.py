from types import SimpleNamespace

from app.model_final_review_ui import _default_relationship_rule


def test_exact_or_unanimous_candidate_is_defaulted():
    relationship = SimpleNamespace(
        candidate_rule_ids=("relationship:dependency",),
    )

    assert _default_relationship_rule(
        relationship,
        ("relationship:dependency", "relationship:traces_to"),
    ) == "relationship:dependency"


def test_unmapped_defaults_to_first_profile_option():
    relationship = SimpleNamespace(candidate_rule_ids=())

    assert _default_relationship_rule(
        relationship,
        ("relationship:dependency", "relationship:traces_to"),
    ) == "relationship:dependency"
