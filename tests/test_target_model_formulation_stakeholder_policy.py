import json
from pathlib import Path


def _find_construct(value, construct_id):
    if isinstance(value, dict):
        if value.get("construct_id") == construct_id:
            return value
        for child in value.values():
            found = _find_construct(child, construct_id)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_construct(child, construct_id)
            if found is not None:
                return found
    return None


def test_tn003_binds_reviewed_stakeholder_role_policy_and_fixture():
    path = Path("context/sysml/sysml_v2_target_notation.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    tn003 = _find_construct(data, "TN_003")
    assert tn003 is not None

    rules = tn003["usage_rules"]
    assert any(
        "standalone reusable stakeholder-role types" in rule
        for rule in rules
    )

    evidence = tn003["syntax_evidence"]
    assert evidence["fixture_id"] == "SFX-C6C3-001"
    assert evidence["fixture_path"] == (
        "context/sysml/fixtures/c6c3/"
        "stakeholder_role_part_definition.sysml"
    )
    assert evidence["validation_environment"] == "SYSIDE"
    assert (
        evidence["validation_status"]
        == "passed_with_nonblocking_warning"
    )
    assert evidence["validation_scope"] == (
        "standalone_part_definition_syntax_only"
    )
    assert evidence["nonblocking_warnings"] == [
        {
            "code": "unused-definition",
            "disposition": (
                "accepted_for_isolated_definition_fixture"
            ),
        }
    ]
