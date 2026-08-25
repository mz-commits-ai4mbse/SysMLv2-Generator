from modules.sysml_generation.authority_backed import (
    AuthorityBackedSysMLArtifactBuilder,
)
from modules.sysml_validation.authority_backed import (
    AuthorityBackedSysMLValidationRepository,
)
from tests.test_authority_backed_sysml_generation import _source_model
from tests.test_authority_backed_sysml_validation import (
    _CompletedExternalValidator,
)


def test_authority_validation_repository_round_trips(tmp_path):
    artifact = AuthorityBackedSysMLArtifactBuilder().build(
        _source_model()
    )
    service = __import__(
        "modules.sysml_validation.authority_backed",
        fromlist=["AuthorityBackedSysMLValidationService"],
    ).AuthorityBackedSysMLValidationService(
        external_validator=_CompletedExternalValidator(),
    )
    repo = AuthorityBackedSysMLValidationRepository(
        tmp_path,
        validation_service=service,
    )

    result = repo.validate(artifact)
    loaded = repo.load(
        "120412",
        artifact.source_internal_engineering_model_id,
    )

    assert loaded == result
    assert result.publication_gate == "passed"
