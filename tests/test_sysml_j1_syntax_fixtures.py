from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("context/sysml/fixtures/j1/syntax_fixture_manifest.json")
TARGET_NOTATION = Path("context/sysml/sysml_v2_target_notation.json")

EXPECTED_VALIDATED_CONSTRUCTS = {
    "SFX-J1-001": ("use_case", "TN_012"),
    "SFX-J1-002": ("dependency", "TN_013"),
    "SFX-J1-003": ("allocated_to", "TN_014"),
    "SFX-J1-004": ("satisfies", "TN_015"),
}


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _load_target_notation() -> dict:
    return json.loads(TARGET_NOTATION.read_text(encoding="utf-8"))


def test_fixture_manifest_is_bound_to_verified_local_reference_commits() -> None:
    payload = _load_manifest()
    baseline = payload["reference_baseline"]

    assert baseline["sysml_v2_release_commit"] == (
        "ee25530ed24b8c93a0e3e4b8d5fbfaa5a8d8ffb4"
    )
    assert baseline["apollo11_commit"] == (
        "6e9c93fe7d80c5ca3534bb14b10ab374a643ef2d"
    )
    assert baseline["apollo_role"] == "non_normative_example_reference"


def test_all_j1_fixtures_record_manual_syside_pass() -> None:
    payload = _load_manifest()
    assert payload["status"] == "syside_validation_passed"

    fixtures = payload["fixtures"]
    assert len(fixtures) == 4
    assert {item["semantic"] for item in fixtures} == {
        "use_case",
        "dependency",
        "allocated_to",
        "satisfies",
    }
    assert all(item["validation_status"] == "passed" for item in fixtures)
    assert all(item["validation_environment"] == "SYSIDE" for item in fixtures)
    assert all(
        item["validation_method"] == "manual_open_and_visualization"
        for item in fixtures
    )
    assert all(item["target_notation_authorized"] is True for item in fixtures)

    # J1 validates/authorizes syntax constructs only. Actual IEM→SysML production
    # permission remains false until J2 adds an explicit Generation Profile rule.
    assert all(item["generation_permission"] is False for item in fixtures)


def test_every_fixture_path_exists() -> None:
    for item in _load_manifest()["fixtures"]:
        assert Path(item["fixture_path"]).is_file()


def test_validated_fixtures_are_explicitly_linked_to_target_notation_constructs() -> None:
    fixtures = {
        item["fixture_id"]: item
        for item in _load_manifest()["fixtures"]
    }
    for fixture_id, (semantic, construct_id) in EXPECTED_VALIDATED_CONSTRUCTS.items():
        fixture = fixtures[fixture_id]
        assert fixture["semantic"] == semantic
        assert fixture["target_notation_construct_id"] == construct_id


def test_target_notation_contains_exactly_the_four_j1_validated_extensions() -> None:
    target = _load_target_notation()
    constructs = {
        item["construct_id"]: item
        for item in target["allowed_constructs"]
    }

    for fixture_id, (_, construct_id) in EXPECTED_VALIDATED_CONSTRUCTS.items():
        assert construct_id in constructs
        evidence = constructs[construct_id]["syntax_evidence"]
        assert evidence["fixture_id"] == fixture_id
        assert evidence["validation_environment"] == "SYSIDE"
        assert evidence["validation_status"] == "passed"
        assert evidence["sysml_v2_release_commit"] == (
            "ee25530ed24b8c93a0e3e4b8d5fbfaa5a8d8ffb4"
        )


def test_use_case_fixture_uses_spec_backed_definition_keyword() -> None:
    text = Path(
        "context/sysml/fixtures/j1/use_case_definition.sysml"
    ).read_text(encoding="utf-8")
    assert "use case def ExampleUseCase" in text
    assert "subject exampleSystem : ExampleSystem;" in text


def test_dependency_fixture_uses_spec_backed_relationship_form() -> None:
    text = Path(
        "context/sysml/fixtures/j1/dependency.sysml"
    ).read_text(encoding="utf-8")
    assert "dependency from source to target;" in text


def test_allocation_fixture_uses_spec_backed_relationship_form() -> None:
    text = Path(
        "context/sysml/fixtures/j1/allocation.sysml"
    ).read_text(encoding="utf-8")
    assert "allocate logicalElement to physicalElement;" in text


def test_satisfaction_fixture_uses_spec_backed_relationship_form() -> None:
    text = Path(
        "context/sysml/fixtures/j1/satisfaction.sysml"
    ).read_text(encoding="utf-8")
    assert "satisfy exampleRequirement by exampleSystem;" in text
