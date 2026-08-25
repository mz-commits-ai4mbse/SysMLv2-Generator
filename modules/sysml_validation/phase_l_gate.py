"""Exact immutable Phase-K → Phase-L publication handoff contract."""

from __future__ import annotations

from modules.sysml_generation.authority_backed import (
    AuthorityBackedGeneratedSysMLArtifactSet,
)
from modules.sysml_validation.authority_backed import (
    validate_authority_backed_artifact_integrity,
)

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .artifact_integrity import calculate_received_artifact_set_fingerprint
from .errors import SysMLValidationContractError
from .service import validate_validation_result_integrity
from .types import SysMLValidationResult


def validate_phase_l_handoff(
    artifact_set: GeneratedSysMLArtifactSet,
    validation_result: SysMLValidationResult,
) -> None:
    """Require the exact K-validated artifact before Phase-L publication.

    This function does not publish anything and does not rerun semantic
    validation. It makes ADR-022 K-21 executable so Phase L can reuse one exact
    fingerprint-bound boundary check.
    """

    if isinstance(artifact_set, GeneratedSysMLArtifactSet):
        received_fingerprint = calculate_received_artifact_set_fingerprint(
            artifact_set
        )
        if received_fingerprint != artifact_set.content_fingerprint:
            raise SysMLValidationContractError(
                "Reviewed artifact content no longer matches its "
                "generation fingerprint."
            )
    elif isinstance(
        artifact_set,
        AuthorityBackedGeneratedSysMLArtifactSet,
    ):
        findings = validate_authority_backed_artifact_integrity(
            artifact_set
        )
        if any(item.blocking for item in findings):
            raise SysMLValidationContractError(
                "Authority-backed reviewed artifact fails its exact "
                "integrity contract."
            )
    else:
        raise SysMLValidationContractError(
            "Final Model Review requires a supported generated SysML "
            "artifact contract."
        )

    if not isinstance(validation_result, SysMLValidationResult):
        raise SysMLValidationContractError(
            "Final Model Review requires a SysMLValidationResult."
        )

    validate_validation_result_integrity(validation_result)

    if validation_result.project_id != artifact_set.project_id:
        raise SysMLValidationContractError(
            "Validation result project does not match the reviewed artifact set."
        )
    if (
        validation_result.source_internal_engineering_model_id
        != artifact_set.source_internal_engineering_model_id
    ):
        raise SysMLValidationContractError(
            "Validation result source IEM does not match the reviewed artifact set."
        )
    if (
        validation_result.source_artifact_set_fingerprint
        != artifact_set.content_fingerprint
    ):
        raise SysMLValidationContractError(
            "Validation result does not authorize this exact reviewed artifact set."
        )
    if (
        validation_result.validation_status != "valid"
        or validation_result.publication_gate != "passed"
    ):
        raise SysMLValidationContractError(
            "Publication requires validation_status=valid and "
            "publication_gate=passed."
        )
