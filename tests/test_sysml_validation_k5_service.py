from __future__ import annotations

from dataclasses import replace

import pytest

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
    SYSML_VALIDATION_RESULT_SCHEMA_VERSION,
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
    SysMLValidationContractError,
    SysMLValidationFinding,
    SysMLValidationLocation,
    SysMLValidationResult,
    SysMLValidationService,
    calculate_json_fingerprint,
    calculate_validation_result_fingerprint,
    validate_validation_result_integrity,
)


def _artifact():
    generation_context = SysMLGenerationContext(
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
    return GeneratedSysMLArtifactSet(
        schema_version="1.0.0",
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        source_iem_content_fingerprint="5" * 64,
        generation_context=generation_context,
        generation_input_fingerprint="6" * 64,
        generation_provenance=SysMLGenerationProvenance(
            method="deterministic_serialization",
            implementation_reference="test",
            context_fingerprint="7" * 64,
        ),
        units=(),
        traceability_entries=(),
        nonblocking_diagnostics=(),
        content_fingerprint="8" * 64,
    )


def _identity(
    *,
    version="0.9.0 (abc123)",
    validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
):
    return SysMLExternalValidatorIdentity(
        validator_id=validator_id,
        tool_name=EXPECTED_EXTERNAL_TOOL_NAME,
        tool_version=version,
        command_contract_id=EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
        configuration_fingerprint=calculate_json_fingerprint(
            SYSIDE_CHECK_COMMAND_CONFIGURATION
        ),
    )


class _ExternalValidator:
    def __init__(
        self,
        *,
        status="completed",
        findings=(),
        version="0.9.0 (abc123)",
        validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
    ):
        self._status = status
        self._findings = tuple(findings)
        self._identity = _identity(version=version, validator_id=validator_id)

    def validate(self, _artifact_set):
        findings = list(self._findings)
        if self._status != "completed" and not any(
            item.category == "validator_infrastructure"
            for item in findings
        ):
            findings.append(
                SysMLValidationFinding(
                    code="K5_TEST_VALIDATOR_INCOMPLETE",
                    category="validator_infrastructure",
                    severity="error",
                    blocking=True,
                    message="Required external validation did not complete.",
                    validator_id=self._identity.validator_id,
                )
            )
        count = sum(
            item.category != "validator_infrastructure"
            for item in findings
        )
        return SysMLExternalValidationRun(
            evidence=SysMLExternalValidationEvidence(
                validator_identity=self._identity,
                execution_status=self._status,
                exit_code=0 if self._status == "completed" else None,
                normalized_diagnostic_count=count,
            ),
            findings=tuple(findings),
        )


def _service(monkeypatch, *, internal_findings=(), **external_kwargs):
    monkeypatch.setattr(
        SysMLValidationService,
        "_run_internal_validation",
        staticmethod(lambda _artifact_set: tuple(internal_findings)),
    )
    return SysMLValidationService(
        external_validator=_ExternalValidator(**external_kwargs)
    )


def _blocking_internal_finding():
    return SysMLValidationFinding(
        code="K5_TEST_INTERNAL_ERROR",
        category="artifact_integrity",
        severity="error",
        blocking=True,
        message="Known deterministic internal validation error.",
    )


def test_k5_valid_result_passes_publication_gate_and_is_fingerprint_bound(monkeypatch):
    artifact = _artifact()
    result = _service(monkeypatch).validate(artifact)
    assert isinstance(result, SysMLValidationResult)
    assert result.schema_version == SYSML_VALIDATION_RESULT_SCHEMA_VERSION
    assert result.project_id == artifact.project_id
    assert result.source_internal_engineering_model_id == (
        artifact.source_internal_engineering_model_id
    )
    assert result.source_artifact_set_fingerprint == artifact.content_fingerprint
    assert result.validation_status == "valid"
    assert result.publication_gate == "passed"
    assert result.findings == ()
    assert result.content_fingerprint == calculate_validation_result_fingerprint(result)
    validate_validation_result_integrity(result)


def test_k5_same_input_and_validator_identity_is_deterministic(monkeypatch):
    artifact = _artifact()
    first = _service(monkeypatch).validate(artifact)
    second = _service(monkeypatch).validate(artifact)
    assert first == second
    assert first.validation_input_fingerprint == second.validation_input_fingerprint
    assert first.content_fingerprint == second.content_fingerprint


def test_k5_external_unavailable_is_incomplete_and_blocks_publication(monkeypatch):
    result = _service(monkeypatch, status="unavailable").validate(_artifact())
    assert result.validation_status == "incomplete"
    assert result.publication_gate == "blocked"
    assert result.external_validator_evidence[0].execution_status == "unavailable"


def test_k5_external_failure_is_incomplete_and_blocks_publication(monkeypatch):
    result = _service(monkeypatch, status="failed").validate(_artifact())
    assert result.validation_status == "incomplete"
    assert result.publication_gate == "blocked"


def test_k5_external_blocking_finding_makes_result_invalid(monkeypatch):
    finding = SysMLValidationFinding(
        code="SYSIDE_TYPE_ERROR",
        category="external_semantics",
        severity="error",
        blocking=True,
        message="Example semantic error",
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        generated_location=SysMLValidationLocation(
            start_line=1,
            end_line=1,
            start_column=1,
        ),
        validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
        validator_rule_id="type-error",
    )
    result = _service(monkeypatch, findings=(finding,)).validate(_artifact())
    assert result.validation_status == "invalid"
    assert result.publication_gate == "blocked"
    assert result.findings == (finding,)


def test_k5_internal_blocking_finding_makes_result_invalid(monkeypatch):
    finding = _blocking_internal_finding()
    result = _service(
        monkeypatch,
        internal_findings=(finding,),
    ).validate(_artifact())
    assert result.validation_status == "invalid"
    assert result.publication_gate == "blocked"
    assert result.findings == (finding,)


def test_k5_known_invalidity_takes_precedence_over_external_incomplete(monkeypatch):
    result = _service(
        monkeypatch,
        internal_findings=(_blocking_internal_finding(),),
        status="unavailable",
    ).validate(_artifact())
    assert result.validation_status == "invalid"
    assert result.publication_gate == "blocked"
    assert result.external_validator_evidence[0].execution_status == "unavailable"


def test_k5_external_warning_remains_visible_and_nonblocking(monkeypatch):
    finding = SysMLValidationFinding(
        code="SYSIDE_EXAMPLE_WARNING",
        category="external_warning",
        severity="warning",
        blocking=False,
        message="Example warning",
        generated_unit_id="GSU-000001",
        generated_location=SysMLValidationLocation(start_line=1, end_line=1),
        validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
        validator_rule_id="example-warning",
    )
    result = _service(monkeypatch, findings=(finding,)).validate(_artifact())
    assert result.validation_status == "valid"
    assert result.publication_gate == "passed"
    assert result.findings == (finding,)


def test_k5_validator_version_changes_validation_input_and_result_identity(monkeypatch):
    artifact = _artifact()
    first = _service(monkeypatch, version="0.9.0 (aaa)").validate(artifact)
    second = _service(monkeypatch, version="0.9.1 (bbb)").validate(artifact)
    assert first.validation_input_fingerprint != second.validation_input_fingerprint
    assert first.content_fingerprint != second.content_fingerprint


def test_k5_result_integrity_rejects_tampered_result_fingerprint(monkeypatch):
    result = _service(monkeypatch).validate(_artifact())
    with pytest.raises(SysMLValidationContractError):
        validate_validation_result_integrity(
            replace(result, content_fingerprint="0" * 64)
        )


def test_k5_rejects_external_validator_identity_outside_pinned_profile(monkeypatch):
    with pytest.raises(SysMLValidationContractError):
        _service(
            monkeypatch,
            validator_id="OTHER_VALIDATOR",
        ).validate(_artifact())



def test_k5_external_unavailable_has_blocking_infrastructure_finding(monkeypatch):
    result = _service(monkeypatch, status="unavailable").validate(_artifact())
    infrastructure = [
        item for item in result.findings
        if item.category == "validator_infrastructure"
    ]
    assert len(infrastructure) == 1
    assert infrastructure[0].severity == "error"
    assert infrastructure[0].blocking is True
    assert result.validation_status == "incomplete"
    assert result.publication_gate == "blocked"


def test_k5_unresolvable_validation_context_is_incomplete(monkeypatch):
    finding = SysMLValidationFinding(
        code="K2_GENERATION_PROFILE_UNRESOLVABLE",
        category="validation_context",
        severity="error",
        blocking=True,
        message="Pinned validation context cannot be resolved.",
    )
    result = _service(
        monkeypatch,
        internal_findings=(finding,),
    ).validate(_artifact())
    assert result.validation_status == "incomplete"
    assert result.publication_gate == "blocked"


def test_k5_service_boundary_returns_validation_result_contract():
    annotations = SysMLValidationService.validate.__annotations__
    assert annotations["return"] in {
        "SysMLValidationResult",
        SysMLValidationResult,
    }
