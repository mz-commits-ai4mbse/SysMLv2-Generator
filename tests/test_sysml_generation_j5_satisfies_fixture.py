from __future__ import annotations

import json
from pathlib import Path

from modules.sysml_generation import find_relationship_mapping, load_generation_profile


FIXTURE = Path("context/sysml/fixtures/j5/satisfies_endpoint_mapping.sysml")
EVIDENCE = Path(
    "context/sysml/fixtures/j5/satisfies_endpoint_mapping_evidence.json"
)


def test_j5_satisfies_fixture_uses_target_by_source_candidate_form() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    assert "satisfy IME_000001 by IME_000002;" in text
    assert "satisfy IME_000001 by IME_000003;" in text
    assert "requirement IME_000001" in text
    assert "part IME_000002" in text
    assert "action IME_000003" in text


def test_j5_satisfies_evidence_records_manual_syside_pass() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == "syside_validation_passed"
    assert evidence["production_generation_permission"] is True
    assert all(
        case["status"] == "passed"
        for case in evidence["validation_cases"]
    )
    assert evidence["proposed_iem_mapping"]["endpoint_rendering"] == (
        "target_by_source"
    )


def test_satisfies_production_mapping_is_enabled_only_after_evidence_pass() -> None:
    profile = load_generation_profile()
    rule = find_relationship_mapping(
        profile,
        relationship_family="refinement",
        semantic_intent="satisfies",
        directionality="source_to_target",
    )
    assert rule is not None
    assert rule["mapping_status"] == "supported"
    assert rule["production_generation_allowed"] is True
    assert rule["endpoint_rendering"] == "target_by_source"
