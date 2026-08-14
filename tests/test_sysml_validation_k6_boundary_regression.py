from __future__ import annotations

from dataclasses import replace
from inspect import signature

import pytest

from modules.sysml_generation.service import SysMLGenerationService
from modules.sysml_generation.types import (
    GeneratedSysMLArtifactSet,
    SysMLArtifactStructureReference,
    SysMLGenerationContext,
    SysMLGenerationProfileReference,
    SysMLGenerationProvenance,
    SysMLGeneratorRulesReference,
    TargetNotationReference,
)
from modules.sysml_validation import (
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
    SYSIDE_CHECK_COMMAND_CONFIGURATION,
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
    SysMLValidationContractError,
    SysMLValidationFinding,
    SysMLValidationResult,
    SysMLValidationService,
    calculate_json_fingerprint,
    calculate_received_artifact_set_fingerprint,
    validate_phase_l_handoff,
)


def _artifact(*, project_id="000001", iem_id="IEM-000001"):
    context = SysMLGenerationContext(
        target_notation_reference=TargetNotationReference(
            context_id="CTX_SYSML_V2_TARGET_NOTATION",
            version="0.2.0",
            content_fingerprint="1" * 64,
        ),
        generation_profile_reference=SysMLGenerationProfileReference(
            profile_id="TURING_SYSML_V2_GENERATION",
            profile_version="1.0.0",
            profile_fingerprint="2" * 64,
        ),
        artifact_structure_reference=SysMLArtifactStructureReference(
            profile_id="TURING_SYSML_V2_ARTIFACT_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="3" * 64,
        ),
        generator_rules_reference=SysMLGeneratorRulesReference(
            rules_id="TURING_SYSML_V2_GENERATOR_RULES",
            rules_version="1.0.0",
            rules_fingerprint="4" * 64,
        ),
    )
    provisional = GeneratedSysMLArtifactSet(
        schema_version="1.0.0",
        project_id=project_id,
        source_internal_engineering_model_id=iem_id,
        source_iem_content_fingerprint="5" * 64,
        generation_context=context,
        generation_input_fingerprint="6" * 64,
        generation_provenance=SysMLGenerationProvenance(
            method="deterministic_serialization",
            implementation_reference="k6-test",
            context_fingerprint="7" * 64,
        ),
        units=(),
        traceability_entries=(),
        nonblocking_diagnostics=(),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_received_artifact_set_fingerprint(
            provisional
        ),
    )


def _identity():
    return SysMLExternalValidatorIdentity(
        validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
        tool_name=EXPECTED_EXTERNAL_TOOL_NAME,
        tool_version="k6-test-validator",
        command_contract_id=EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
        configuration_fingerprint=calculate_json_fingerprint(
            SYSIDE_CHECK_COMMAND_CONFIGURATION
        ),
    )


class _ExternalValidator:
    def __init__(self, *, status="completed", findings=()):
        self.status = status
        self.findings = tuple(findings)
        self.identity = _identity()

    def validate(self, _artifact_set):
        findings = list(self.findings)
        if self.status != "completed":
            findings.append(
                SysMLValidationFinding(
                    code="K6_VALIDATOR_INCOMPLETE",
                    category="validator_infrastructure",
                    severity="error",
                    blocking=True,
                    message="K6 external validator did not complete.",
                    validator_id=self.identity.validator_id,
                )
            )
        return SysMLExternalValidationRun(
            evidence=SysMLExternalValidationEvidence(
                validator_identity=self.identity,
                execution_status=self.status,
                exit_code=0 if self.status == "completed" else None,
                normalized_diagnostic_count=sum(
                    item.category != "validator_infrastructure"
                    for item in findings
                ),
            ),
            findings=tuple(findings),
        )


def _service(monkeypatch, *, status="completed", internal_findings=()):
    monkeypatch.setattr(
        SysMLValidationService,
        "_run_internal_validation",
        staticmethod(lambda _artifact_set: tuple(internal_findings)),
    )
    return SysMLValidationService(
        external_validator=_ExternalValidator(status=status)
    )


def test_k6_j_to_k_public_boundary_types_are_exact():
    j_annotations = SysMLGenerationService.generate.__annotations__
    assert j_annotations["return"] in {
        "GeneratedSysMLArtifactSet",
        GeneratedSysMLArtifactSet,
    }

    k_signature = signature(SysMLValidationService.validate)
    assert tuple(k_signature.parameters) == ("self", "artifact_set")
    assert k_signature.parameters["artifact_set"].annotation in {
        "GeneratedSysMLArtifactSet",
        GeneratedSysMLArtifactSet,
    }
    assert k_signature.return_annotation in {
        "SysMLValidationResult",
        SysMLValidationResult,
    }


def test_k6_exact_valid_artifact_is_phase_l_eligible(monkeypatch):
    artifact = _artifact()
    result = _service(monkeypatch).validate(artifact)
    assert validate_phase_l_handoff(artifact, result) is None


def test_k6_different_artifact_fingerprint_cannot_reuse_validation(monkeypatch):
    artifact = _artifact()
    result = _service(monkeypatch).validate(artifact)
    other_artifact = _artifact(project_id="000002")
    with pytest.raises(SysMLValidationContractError):
        validate_phase_l_handoff(other_artifact, result)


def test_k6_tampered_artifact_cannot_reuse_validation(monkeypatch):
    artifact = _artifact()
    result = _service(monkeypatch).validate(artifact)
    tampered = replace(artifact, project_id="000002")
    with pytest.raises(SysMLValidationContractError):
        validate_phase_l_handoff(tampered, result)


def test_k6_incomplete_validation_cannot_enter_phase_l(monkeypatch):
    artifact = _artifact()
    result = _service(monkeypatch, status="unavailable").validate(artifact)
    assert result.validation_status == "incomplete"
    assert result.publication_gate == "blocked"
    with pytest.raises(SysMLValidationContractError):
        validate_phase_l_handoff(artifact, result)


def test_k6_invalid_validation_cannot_enter_phase_l(monkeypatch):
    artifact = _artifact()
    finding = SysMLValidationFinding(
        code="K6_MODEL_DEFECT",
        category="relationship_consistency",
        severity="error",
        blocking=True,
        message="Known generated-model defect.",
    )
    result = _service(
        monkeypatch,
        internal_findings=(finding,),
    ).validate(artifact)
    assert result.validation_status == "invalid"
    assert result.publication_gate == "blocked"
    with pytest.raises(SysMLValidationContractError):
        validate_phase_l_handoff(artifact, result)
