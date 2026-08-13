from __future__ import annotations

import json
from pathlib import Path

from modules.sysml_generation import (
    PHASE_J_TARGET_NOTATION_VERSION,
    load_target_notation,
    load_target_notation_reference,
)


TARGET = Path("context/sysml/sysml_v2_target_notation.json")


def test_target_notation_is_phase_j_version_020() -> None:
    payload = load_target_notation(TARGET)
    assert payload["version"] == PHASE_J_TARGET_NOTATION_VERSION
    assert payload["version"] == "0.2.0"


def test_target_notation_uses_only_explicit_iem_as_direct_generation_input() -> None:
    payload = load_target_notation(TARGET)
    rules = payload["artifact_generation_rules"]

    assert rules["required_generation_input"] == (
        "validated_explicit_internal_engineering_model_snapshot"
    )
    assert rules["generation_input_service"].startswith(
        "InternalModelReadService.load_phase_j_input"
    )
    assert rules["internal_engineering_model_required"] is True
    assert rules["raw_legacy_data_allowed_as_direct_generation_input"] is False
    assert rules["approved_input_allowed_as_direct_generation_input"] is False
    assert rules["candidate_artifacts_allowed_as_direct_generation_input"] is False


def test_target_notation_preserves_j_k_l_boundary() -> None:
    payload = load_target_notation(TARGET)
    rules = payload["artifact_generation_rules"]

    assert rules["phase_j_result"] == "GeneratedSysMLArtifactSet"
    assert rules["phase_k_validation_required_before_publication"] is True
    assert rules["final_publication_phase"] == "L"
    assert rules["final_published_output_folder"] == "data/output/"


def test_pending_syntax_evidence_does_not_grant_generation_permission() -> None:
    payload = load_target_notation(TARGET)
    evidence = payload["syntax_evidence_policy"]

    assert evidence["target_environment"] == "SYSIDE"
    assert evidence["pending_fixture_grants_generation_permission"] is False
    assert evidence["fixture_manifest"] == (
        "context/sysml/fixtures/j1/syntax_fixture_manifest.json"
    )


def test_old_direct_generation_vocabulary_is_removed() -> None:
    payload = json.loads(TARGET.read_text(encoding="utf-8"))
    rules = payload["artifact_generation_rules"]

    assert "approved_model_data_required" not in rules
    assert "required_input_state_for_sysml_generation" not in rules
    assert "generated_output_folder" not in rules


def test_target_notation_reference_is_canonical_and_pinned() -> None:
    first = load_target_notation_reference(TARGET)
    second = load_target_notation_reference(TARGET)

    assert first == second
    assert first.context_id == "CTX_SYSML_V2_TARGET_NOTATION"
    assert first.version == "0.2.0"
    assert len(first.content_fingerprint) == 64
