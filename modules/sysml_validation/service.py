"""Phase-K orchestration, status/gate policy and deterministic result identity."""

from __future__ import annotations

from dataclasses import asdict, replace

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .artifact_integrity import validate_artifact_set_integrity
from .artifact_structure_validator import validate_artifact_structure
from .errors import SysMLValidationContractError
from .external_validator import SysMLExternalValidator
from .finding_support import sort_validation_findings
from .fingerprints import calculate_json_fingerprint, validate_sha256_fingerprint
from .relationship_validator import validate_relationship_consistency
from .syside_cli import SysideCliValidator
from .target_notation_validator import validate_target_notation_subset
from .traceability import validate_traceability
from .types import (
    EXTERNAL_VALIDATOR_EXECUTION_STATUSES,
    PUBLICATION_GATES,
    VALIDATION_STATUSES,
    SysMLExternalValidationEvidence,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationProfileReference,
    SysMLValidationResult,
)
from .validation_context import validate_generation_context
from .validation_profile import load_validation_profile


SYSML_VALIDATION_RESULT_SCHEMA_VERSION = "1.0.0"


def calculate_validation_input_fingerprint(
    *,
    source_artifact_set_fingerprint: str,
    validation_profile_reference: SysMLValidationProfileReference,
    external_validator_identity: SysMLExternalValidatorIdentity,
) -> str:
    """Fingerprint the exact artifact/policy/external-environment validation input."""

    validate_sha256_fingerprint(
        source_artifact_set_fingerprint,
        label="source artifact-set fingerprint",
    )
    validate_sha256_fingerprint(
        validation_profile_reference.profile_fingerprint,
        label="validation profile fingerprint",
    )
    validate_sha256_fingerprint(
        external_validator_identity.configuration_fingerprint,
        label="external validator configuration fingerprint",
    )
    return calculate_json_fingerprint(
        {
            "source_artifact_set_fingerprint": source_artifact_set_fingerprint,
            "validation_profile_reference": asdict(validation_profile_reference),
            "external_validator_identity": asdict(external_validator_identity),
            "external_validator_configuration_fingerprint": (
                external_validator_identity.configuration_fingerprint
            ),
            "command_contract_id": external_validator_identity.command_contract_id,
        }
    )


def calculate_validation_result_fingerprint(
    result: SysMLValidationResult,
) -> str:
    """Recalculate the deterministic identity of a Phase-K result."""

    return calculate_json_fingerprint(_validation_result_payload(result))


def validate_validation_result_integrity(
    result: SysMLValidationResult,
) -> None:
    """Validate the immutable K→L result contract and its deterministic identity."""

    if not isinstance(result, SysMLValidationResult):
        raise SysMLValidationContractError(
            "Phase-K result must be a SysMLValidationResult."
        )
    if result.schema_version != SYSML_VALIDATION_RESULT_SCHEMA_VERSION:
        raise SysMLValidationContractError(
            "Unsupported SysMLValidationResult schema_version."
        )
    if result.validation_status not in VALIDATION_STATUSES:
        raise SysMLValidationContractError("Invalid Phase-K validation_status.")
    if result.publication_gate not in PUBLICATION_GATES:
        raise SysMLValidationContractError("Invalid Phase-K publication_gate.")

    for value, label in (
        (result.source_artifact_set_fingerprint, "source artifact-set fingerprint"),
        (
            result.validation_profile_reference.profile_fingerprint,
            "validation profile fingerprint",
        ),
        (result.validation_input_fingerprint, "validation input fingerprint"),
        (result.content_fingerprint, "validation result fingerprint"),
    ):
        validate_sha256_fingerprint(value, label=label)

    if len(result.external_validator_evidence) != 1:
        raise SysMLValidationContractError(
            "Phase-K 1.0.0 requires exactly one external validator evidence record."
        )
    profile = load_validation_profile()
    if result.validation_profile_reference != _profile_reference(profile):
        raise SysMLValidationContractError(
            "Validation Profile reference/fingerprint does not match the exact resolved policy."
        )
    for evidence in result.external_validator_evidence:
        _validate_external_evidence(evidence)
        _validate_external_identity_against_profile(
            evidence.validator_identity,
            profile=profile,
        )

    if result.findings != sort_validation_findings(result.findings):
        raise SysMLValidationContractError(
            "Phase-K findings are not in canonical deterministic order."
        )

    external_complete = all(
        item.execution_status == "completed"
        for item in result.external_validator_evidence
    )
    if not external_complete and not any(
        item.blocking and item.category == "validator_infrastructure"
        for item in result.findings
    ):
        raise SysMLValidationContractError(
            "Incomplete external validation requires an explicit blocking "
            "validator_infrastructure finding."
        )
    expected_status, expected_gate = _status_and_gate(
        findings=result.findings,
        external_complete=external_complete,
    )
    if (
        result.validation_status != expected_status
        or result.publication_gate != expected_gate
    ):
        raise SysMLValidationContractError(
            "Phase-K validation_status/publication_gate do not match findings "
            "and required external-validator completion."
        )

    expected_input = calculate_validation_input_fingerprint(
        source_artifact_set_fingerprint=result.source_artifact_set_fingerprint,
        validation_profile_reference=result.validation_profile_reference,
        external_validator_identity=(
            result.external_validator_evidence[0].validator_identity
        ),
    )
    if expected_input != result.validation_input_fingerprint:
        raise SysMLValidationContractError(
            "Phase-K validation_input_fingerprint mismatch."
        )

    if calculate_validation_result_fingerprint(result) != result.content_fingerprint:
        raise SysMLValidationContractError(
            "SysMLValidationResult content_fingerprint mismatch."
        )


class SysMLValidationService:
    """Validate one explicit Phase-J artifact set without re-reading upstream state."""

    def __init__(
        self,
        *,
        external_validator: SysMLExternalValidator | None = None,
    ) -> None:
        self._external_validator = (
            external_validator
            if external_validator is not None
            else SysideCliValidator()
        )

    def validate(
        self,
        artifact_set: GeneratedSysMLArtifactSet,
    ) -> SysMLValidationResult:
        """Run deterministic internal checks plus required external validation."""

        if not isinstance(artifact_set, GeneratedSysMLArtifactSet):
            raise SysMLValidationContractError(
                "SysMLValidationService requires a GeneratedSysMLArtifactSet."
            )

        # Loading the profile is itself a strict configuration gate. K does not
        # silently substitute another version or continue with an invalid policy.
        profile = load_validation_profile()
        profile_reference = _profile_reference(profile)

        internal_findings = self._run_internal_validation(artifact_set)
        external_run = self._external_validator.validate(artifact_set)
        _validate_external_evidence(external_run.evidence)
        _validate_external_identity_against_profile(
            external_run.evidence.validator_identity,
            profile=profile,
        )

        findings = sort_validation_findings(
            (*internal_findings, *external_run.findings)
        )
        external_complete = external_run.evidence.execution_status == "completed"
        if not external_complete and not any(
            item.blocking and item.category == "validator_infrastructure"
            for item in findings
        ):
            raise SysMLValidationContractError(
                "Incomplete external validation requires an explicit blocking "
                "validator_infrastructure finding."
            )
        validation_status, publication_gate = _status_and_gate(
            findings=findings,
            external_complete=external_complete,
        )

        # The profile loader has already validated the exact 1.0.0 values; use
        # those values rather than hard-coding a second policy source here.
        publication = profile["publication_policy"]
        if validation_status == "valid":
            validation_status = publication["pass_validation_status"]
            publication_gate = publication["pass_publication_gate"]
        elif validation_status == "incomplete":
            validation_status = publication["incomplete_validation_status"]
            publication_gate = publication["incomplete_publication_gate"]
        else:
            publication_gate = publication["blocking_finding_gate"]

        validation_input_fingerprint = calculate_validation_input_fingerprint(
            source_artifact_set_fingerprint=artifact_set.content_fingerprint,
            validation_profile_reference=profile_reference,
            external_validator_identity=external_run.evidence.validator_identity,
        )

        provisional = SysMLValidationResult(
            schema_version=SYSML_VALIDATION_RESULT_SCHEMA_VERSION,
            project_id=artifact_set.project_id,
            source_internal_engineering_model_id=(
                artifact_set.source_internal_engineering_model_id
            ),
            source_artifact_set_fingerprint=artifact_set.content_fingerprint,
            validation_profile_reference=profile_reference,
            validation_input_fingerprint=validation_input_fingerprint,
            external_validator_evidence=(external_run.evidence,),
            findings=findings,
            validation_status=validation_status,
            publication_gate=publication_gate,
            content_fingerprint="0" * 64,
        )
        result = replace(
            provisional,
            content_fingerprint=calculate_validation_result_fingerprint(provisional),
        )
        validate_validation_result_integrity(result)
        return result

    @staticmethod
    def _run_internal_validation(
        artifact_set: GeneratedSysMLArtifactSet,
    ) -> tuple[SysMLValidationFinding, ...]:
        """Run K2/K3 validators without re-loading the source IEM.

        `validate_generation_context` contains both exact Phase-J policy-reference
        resolution and the Model Structure / Comparability profile-chain check.
        Thus it satisfies the two profile entries `generation_context` and
        `model_structure_comparability` without duplicate findings or an upstream
        Candidate/IEM reinterpretation.
        """

        findings: list[SysMLValidationFinding] = []
        for validator in (
            validate_artifact_set_integrity,
            validate_generation_context,
            validate_target_notation_subset,
            validate_artifact_structure,
            validate_traceability,
            validate_relationship_consistency,
        ):
            findings.extend(validator(artifact_set))
        return sort_validation_findings(findings)


_INCOMPLETE_CONTEXT_CODES = frozenset(
    {
        "K2_TARGET_NOTATION_UNRESOLVABLE",
        "K2_GENERATION_PROFILE_UNRESOLVABLE",
        "K2_ARTIFACT_STRUCTURE_UNRESOLVABLE",
        "K2_GENERATOR_RULES_UNRESOLVABLE",
        "K2_GENERATION_PROFILE_CHAIN_UNRESOLVABLE",
        "K2_ARTIFACT_STRUCTURE_CHAIN_UNRESOLVABLE",
        "K2_MODEL_STRUCTURE_PROFILE_UNRESOLVABLE",
    }
)


def _status_and_gate(
    *,
    findings: tuple[SysMLValidationFinding, ...],
    external_complete: bool,
) -> tuple[str, str]:
    # A proven generated-model/artifact defect remains invalid even if another
    # required validation layer is incomplete. Infrastructure and unresolved
    # validation-context findings still block publication, but they describe an
    # incomplete validation environment rather than an invalid model.
    has_invalid_blocking = any(
        item.blocking
        and item.category != "validator_infrastructure"
        and item.code not in _INCOMPLETE_CONTEXT_CODES
        for item in findings
    )
    has_incomplete_blocking = any(
        item.blocking
        and (
            item.category == "validator_infrastructure"
            or item.code in _INCOMPLETE_CONTEXT_CODES
        )
        for item in findings
    )
    if has_invalid_blocking:
        return "invalid", "blocked"
    if not external_complete or has_incomplete_blocking:
        return "incomplete", "blocked"
    return "valid", "passed"


def _validate_external_evidence(
    evidence: SysMLExternalValidationEvidence,
) -> None:
    if evidence.execution_status not in EXTERNAL_VALIDATOR_EXECUTION_STATUSES:
        raise SysMLValidationContractError(
            "External validator evidence has invalid execution_status."
        )
    identity = evidence.validator_identity
    if not identity.validator_id.strip() or not identity.tool_name.strip():
        raise SysMLValidationContractError(
            "External validator identity must contain validator/tool identity."
        )
    if not identity.command_contract_id.strip():
        raise SysMLValidationContractError(
            "External validator command contract must be non-empty."
        )
    validate_sha256_fingerprint(
        identity.configuration_fingerprint,
        label="external validator configuration fingerprint",
    )
    if (
        not isinstance(evidence.normalized_diagnostic_count, int)
        or isinstance(evidence.normalized_diagnostic_count, bool)
        or evidence.normalized_diagnostic_count < 0
    ):
        raise SysMLValidationContractError(
            "normalized_diagnostic_count must be a non-negative integer."
        )
    if evidence.exit_code is not None and (
        not isinstance(evidence.exit_code, int)
        or isinstance(evidence.exit_code, bool)
    ):
        raise SysMLValidationContractError(
            "External validator exit_code must be integer or null."
        )




def _profile_reference(profile: dict[str, object]) -> SysMLValidationProfileReference:
    return SysMLValidationProfileReference(
        profile_id=str(profile["profile_id"]),
        profile_version=str(profile["profile_version"]),
        profile_fingerprint=calculate_json_fingerprint(profile),
    )


def _validate_external_identity_against_profile(
    identity: SysMLExternalValidatorIdentity,
    *,
    profile: dict[str, object],
) -> None:
    external = profile["external_validator"]
    assert isinstance(external, dict)
    if identity.validator_id != external["validator_id"]:
        raise SysMLValidationContractError(
            "External validator identity does not match the pinned Validation Profile."
        )
    if identity.tool_name != external["tool_name"]:
        raise SysMLValidationContractError(
            "External validator tool does not match the pinned Validation Profile."
        )
    if identity.command_contract_id != external["command_contract_id"]:
        raise SysMLValidationContractError(
            "External validator command contract does not match the pinned Validation Profile."
        )


def _validation_result_payload(result: SysMLValidationResult) -> dict[str, object]:
    return {
        "schema_version": result.schema_version,
        "project_id": result.project_id,
        "source_internal_engineering_model_id": (
            result.source_internal_engineering_model_id
        ),
        "source_artifact_set_fingerprint": result.source_artifact_set_fingerprint,
        "validation_profile_reference": asdict(result.validation_profile_reference),
        "validation_input_fingerprint": result.validation_input_fingerprint,
        "external_validator_evidence": [
            asdict(item) for item in result.external_validator_evidence
        ],
        "findings": [asdict(item) for item in result.findings],
        "validation_status": result.validation_status,
        "publication_gate": result.publication_gate,
    }
