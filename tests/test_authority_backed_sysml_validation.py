from types import SimpleNamespace

from modules.sysml_generation.authority_backed import (
    AuthorityBackedSysMLArtifactBuilder,
)
from modules.sysml_validation.authority_backed import (
    AuthorityBackedSysMLValidationService,
    validate_authority_backed_traceability,
)
from modules.sysml_validation.types import (
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
)
from modules.sysml_validation.validation_profile import (
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
)

from tests.test_authority_backed_sysml_generation import _source_model


class _CompletedExternalValidator:
    def validate(self, artifact_set):
        identity = SysMLExternalValidatorIdentity(
            validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
            tool_name=EXPECTED_EXTERNAL_TOOL_NAME,
            tool_version="test",
            command_contract_id=(
                EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID
            ),
            configuration_fingerprint="f" * 64,
        )
        evidence = SysMLExternalValidationEvidence(
            validator_identity=identity,
            execution_status="completed",
            exit_code=0,
            normalized_diagnostic_count=0,
        )
        return SysMLExternalValidationRun(
            evidence=evidence,
            findings=(),
        )


def _artifact():
    return AuthorityBackedSysMLArtifactBuilder().build(
        _source_model()
    )


def test_authority_backed_validation_passes_without_candidate_review():
    result = AuthorityBackedSysMLValidationService(
        external_validator=_CompletedExternalValidator(),
    ).validate(_artifact())

    assert result.validation_status == "valid"
    assert result.publication_gate == "passed"
    assert result.findings == ()


def test_authority_traceability_accepts_mpd_without_mcd():
    artifact = _artifact()

    assert validate_authority_backed_traceability(
        artifact
    ) == ()
    trace = artifact.traceability_entries[0]
    assert trace.authority_references[0].authority_id.startswith(
        "MPD-"
    )
