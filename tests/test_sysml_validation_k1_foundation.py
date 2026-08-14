from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from modules.sysml_validation import (
    EXTERNAL_VALIDATOR_EXECUTION_STATUSES,
    PUBLICATION_GATES,
    VALIDATION_FINDING_CATEGORIES,
    VALIDATION_SEVERITIES,
    VALIDATION_STATUSES,
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_VALIDATION_PROFILE_ID,
    EXPECTED_VALIDATION_PROFILE_VERSION,
    SysMLExternalValidationEvidence,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationLocation,
    SysMLValidationProfileError,
    SysMLValidationProfileReference,
    SysMLValidationResult,
    calculate_json_fingerprint,
    calculate_validation_profile_fingerprint,
    load_validation_profile,
    load_validation_profile_reference,
    validate_validation_profile,
)


PROFILE_PATH = Path("context/sysml/turing_sysml_v2_validation_profile.json")
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _profile() -> dict[str, object]:
    return load_validation_profile(PROFILE_PATH)


def test_k1_profile_identity_and_external_validator_contract_are_pinned() -> None:
    profile = _profile()

    assert profile["profile_id"] == EXPECTED_VALIDATION_PROFILE_ID
    assert profile["profile_version"] == EXPECTED_VALIDATION_PROFILE_VERSION
    external = profile["external_validator"]
    assert isinstance(external, dict)
    assert external["validator_id"] == EXPECTED_EXTERNAL_VALIDATOR_ID
    assert external["tool_name"] == EXPECTED_EXTERNAL_TOOL_NAME
    assert external["command_contract_id"] == EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID
    assert external["required"] is True
    assert external["unavailable_validation_status"] == "incomplete"
    assert external["unavailable_publication_gate"] == "blocked"


def test_k1_profile_declares_all_required_internal_validators_in_canonical_order() -> None:
    profile = _profile()

    validators = profile["required_internal_validators"]
    assert isinstance(validators, list)
    assert [(item["validator_id"], item["category"]) for item in validators] == [
        ("artifact_set_integrity", "artifact_integrity"),
        ("generation_context", "validation_context"),
        ("target_notation", "target_notation"),
        ("artifact_structure", "artifact_structure"),
        ("traceability", "traceability"),
        ("model_structure_comparability", "validation_context"),
        ("relationship_consistency", "relationship_consistency"),
    ]
    assert all(item["required"] is True for item in validators)


def test_k1_controlled_vocabularies_match_accepted_architecture() -> None:
    assert VALIDATION_STATUSES == ("valid", "invalid", "incomplete")
    assert PUBLICATION_GATES == ("passed", "blocked")
    assert VALIDATION_SEVERITIES == ("info", "warning", "error")
    assert EXTERNAL_VALIDATOR_EXECUTION_STATUSES == (
        "completed",
        "unavailable",
        "failed",
    )
    assert VALIDATION_FINDING_CATEGORIES == (
        "artifact_integrity",
        "validation_context",
        "target_notation",
        "artifact_structure",
        "relationship_consistency",
        "traceability",
        "external_syntax",
        "external_semantics",
        "external_warning",
        "validator_infrastructure",
    )


def test_k1_warning_and_fail_closed_publication_policy_are_pinned() -> None:
    profile = _profile()

    severity = profile["severity_policy"]
    publication = profile["publication_policy"]
    assert isinstance(severity, dict)
    assert isinstance(publication, dict)
    assert severity["default_blocking_by_severity"] == {
        "info": False,
        "warning": False,
        "error": True,
    }
    assert severity["external_warning_blocking"] is False
    assert publication == {
        "pass_validation_status": "valid",
        "pass_publication_gate": "passed",
        "blocking_finding_gate": "blocked",
        "incomplete_validation_status": "incomplete",
        "incomplete_publication_gate": "blocked",
    }


def test_k1_profile_fingerprint_is_canonical_and_reference_is_exact() -> None:
    profile = _profile()
    expected = calculate_json_fingerprint(profile)

    assert calculate_validation_profile_fingerprint(profile) == expected
    assert load_validation_profile_reference(PROFILE_PATH) == (
        SysMLValidationProfileReference(
            profile_id=EXPECTED_VALIDATION_PROFILE_ID,
            profile_version=EXPECTED_VALIDATION_PROFILE_VERSION,
            profile_fingerprint=expected,
        )
    )


def test_k1_profile_fingerprint_is_independent_of_json_key_order() -> None:
    profile = _profile()
    reordered = dict(reversed(list(profile.items())))

    assert calculate_validation_profile_fingerprint(reordered) == (
        calculate_validation_profile_fingerprint(profile)
    )


def test_k1_profile_rejects_unknown_root_field() -> None:
    profile = _profile()
    profile["unexpected"] = True

    with pytest.raises(SysMLValidationProfileError, match="unknown=.*unexpected"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_missing_root_field() -> None:
    profile = _profile()
    del profile["fingerprint_policy"]

    with pytest.raises(SysMLValidationProfileError, match="missing=.*fingerprint_policy"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_reordered_internal_validator_contract() -> None:
    profile = _profile()
    validators = list(profile["required_internal_validators"])
    validators[0], validators[1] = validators[1], validators[0]
    profile["required_internal_validators"] = validators

    with pytest.raises(SysMLValidationProfileError, match="canonical order"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_nonrequired_internal_validator() -> None:
    profile = _profile()
    validators = [dict(item) for item in profile["required_internal_validators"]]
    validators[0]["required"] = False
    profile["required_internal_validators"] = validators

    with pytest.raises(SysMLValidationProfileError, match="required=true"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_validator_unavailability_as_success() -> None:
    profile = _profile()
    external = dict(profile["external_validator"])
    external["unavailable_validation_status"] = "valid"
    profile["external_validator"] = external

    with pytest.raises(SysMLValidationProfileError, match="status 'incomplete'"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_external_warning_as_blocking_default() -> None:
    profile = _profile()
    severity = dict(profile["severity_policy"])
    severity["external_warning_blocking"] = True
    profile["severity_policy"] = severity

    with pytest.raises(SysMLValidationProfileError, match="must be false"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_noncanonical_finding_order() -> None:
    profile = _profile()
    normalization = dict(profile["diagnostic_normalization"])
    order = list(normalization["canonical_finding_order"])
    order.reverse()
    normalization["canonical_finding_order"] = order
    profile["diagnostic_normalization"] = normalization

    with pytest.raises(SysMLValidationProfileError, match="canonical_finding_order"):
        validate_validation_profile(profile)


def test_k1_loader_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    target = tmp_path / "duplicate.json"
    target.write_text(
        '{"schema_version":"1.0.0","schema_version":"1.0.0"}',
        encoding="utf-8",
    )

    with pytest.raises(SysMLValidationProfileError, match="Duplicate JSON key"):
        load_validation_profile(target)


def test_k1_domain_contracts_are_frozen() -> None:
    reference = SysMLValidationProfileReference(
        profile_id=EXPECTED_VALIDATION_PROFILE_ID,
        profile_version=EXPECTED_VALIDATION_PROFILE_VERSION,
        profile_fingerprint=SHA_A,
    )

    with pytest.raises(FrozenInstanceError):
        reference.profile_version = "9.9.9"  # type: ignore[misc]


def test_k1_domain_contract_can_represent_valid_result_without_runtime_metadata() -> None:
    reference = SysMLValidationProfileReference(
        profile_id=EXPECTED_VALIDATION_PROFILE_ID,
        profile_version=EXPECTED_VALIDATION_PROFILE_VERSION,
        profile_fingerprint=SHA_A,
    )
    identity = SysMLExternalValidatorIdentity(
        validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
        tool_name="SYSIDE Modeler CLI",
        tool_version="test-version",
        command_contract_id=EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
        configuration_fingerprint=SHA_B,
    )
    evidence = SysMLExternalValidationEvidence(
        validator_identity=identity,
        execution_status="completed",
        exit_code=0,
        normalized_diagnostic_count=0,
    )
    result = SysMLValidationResult(
        schema_version="1.0.0",
        project_id="PROJECT_000001",
        source_internal_engineering_model_id="IEM_000001",
        source_artifact_set_fingerprint=SHA_C,
        validation_profile_reference=reference,
        validation_input_fingerprint=SHA_D,
        external_validator_evidence=(evidence,),
        findings=(),
        validation_status="valid",
        publication_gate="passed",
        content_fingerprint=SHA_A,
    )

    assert result.validation_status == "valid"
    assert result.publication_gate == "passed"
    assert not hasattr(result, "timestamp")
    assert not hasattr(result, "temporary_workspace_path")


def test_k1_finding_contract_can_reference_normalized_generated_location() -> None:
    finding = SysMLValidationFinding(
        code="K2_EXAMPLE",
        category="artifact_integrity",
        severity="error",
        blocking=True,
        message="Example deterministic finding.",
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        generated_location=SysMLValidationLocation(
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=9,
        ),
        validator_id="artifact_set_integrity",
        validator_rule_id="EXAMPLE_RULE",
    )

    assert finding.generated_location is not None
    assert finding.generated_location.start_line == 10
    assert finding.blocking is True


def test_k1_profile_rejects_nonlist_controlled_sequence() -> None:
    profile = _profile()
    severity = dict(profile["severity_policy"])
    severity["allowed_severities"] = 42
    profile["severity_policy"] = severity

    with pytest.raises(SysMLValidationProfileError, match="list of strings"):
        validate_validation_profile(profile)


def test_k1_profile_rejects_wrong_external_tool_name() -> None:
    profile = _profile()
    external = dict(profile["external_validator"])
    external["tool_name"] = "Some Other Validator"
    profile["external_validator"] = external

    with pytest.raises(SysMLValidationProfileError, match="Unexpected external tool_name"):
        validate_validation_profile(profile)
