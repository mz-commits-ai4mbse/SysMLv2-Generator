"""Tests for exact derivation-rules context references."""

import json

import pytest

from modules.model_candidates import (
    ModelCandidateValidationError,
    load_model_derivation_rules_reference,
)


def test_derivation_rules_reference_is_exact_and_stable():
    first = load_model_derivation_rules_reference()
    second = load_model_derivation_rules_reference()
    assert first == second
    assert first.context_id == "CTX_SYSML_MODEL_DERIVATION_RULES"
    assert first.context_version == "0.1.0"
    assert len(first.context_fingerprint) == 64


def test_derivation_rules_reference_rejects_missing_global_rule(tmp_path):
    payload = {
        "context_id": "CTX_SYSML_MODEL_DERIVATION_RULES",
        "version": "0.1.0",
        "decision_levels": [
            {"level": "supported"},
            {"level": "partially_supported"},
            {"level": "not_supported"},
            {"level": "conflicting"},
        ],
        "global_generation_rules": [
            {"rule_id": f"DERIVATION_RULE_{n:03d}"}
            for n in range(1, 8)
        ],
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ModelCandidateValidationError):
        load_model_derivation_rules_reference(path)
