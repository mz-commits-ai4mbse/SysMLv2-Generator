from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from modules.final_model_review.read_model import FinalModelReviewReadService
from modules.final_model_review.repository import _default_artifact_validator
from modules.output_publication.final_review_publication import (
    FinalReviewPublicationService,
)
from modules.sysml_generation.authority_backed import (
    AuthorityBackedGeneratedSysMLArtifactSet,
    AuthorityBackedSysMLArtifactBuilder,
)
from modules.sysml_validation.authority_backed import (
    AuthorityBackedSysMLValidationService,
)
from modules.sysml_validation.errors import SysMLValidationContractError
from modules.sysml_validation.phase_l_gate import validate_phase_l_handoff

from tests.test_authority_backed_sysml_generation import _source_model
from tests.test_authority_backed_sysml_validation import (
    _CompletedExternalValidator,
)


def _artifact():
    return AuthorityBackedSysMLArtifactBuilder().build(_source_model())


def _validation(artifact):
    return AuthorityBackedSysMLValidationService(
        external_validator=_CompletedExternalValidator(),
    ).validate(artifact)


def test_authority_backed_artifact_crosses_exact_final_review_gate():
    artifact = _artifact()
    validation = _validation(artifact)

    _default_artifact_validator(artifact)
    assert validate_phase_l_handoff(artifact, validation) is None


def test_tampered_authority_backed_artifact_is_rejected():
    artifact = _artifact()
    validation = _validation(artifact)
    tampered = replace(artifact, content_fingerprint="0" * 64)

    with pytest.raises(SysMLValidationContractError):
        validate_phase_l_handoff(tampered, validation)


def test_publication_reconstructs_exact_authority_backed_artifact():
    artifact = _artifact()
    bundle = SimpleNamespace(
        artifact_set_snapshot=asdict(artifact),
        generated_units=tuple(
            SimpleNamespace(
                generated_unit_id=unit.unit_id,
                relative_path=unit.relative_path,
                content=unit.content,
                content_fingerprint=unit.content_fingerprint,
            )
            for unit in artifact.units
        ),
    )

    service = object.__new__(FinalReviewPublicationService)
    reconstructed = service._artifact_set_from_bundle(bundle)

    assert isinstance(
        reconstructed,
        AuthorityBackedGeneratedSysMLArtifactSet,
    )
    assert reconstructed == artifact


def test_final_review_traceability_preserves_human_authority():
    artifact = _artifact()
    service = object.__new__(FinalModelReviewReadService)

    traces = service._traceability(asdict(artifact))

    element_trace = next(
        item
        for item in traces
        if item.source_internal_model_element_id is not None
    )
    assert element_trace.source_model_candidate_id is None
    assert element_trace.approved_input_ids
    assert any(
        value.startswith("MPD-")
        for value in element_trace.authority_ids
    )

    relationship_traces = tuple(
        item
        for item in traces
        if item.source_internal_model_relationship_id is not None
    )
    if relationship_traces:
        relationship_trace = relationship_traces[0]
        assert relationship_trace.source_model_candidate_id is None
        assert any(
            value.startswith("SRD-")
            for value in relationship_trace.authority_ids
        )
        assert any(
            value.startswith("FAD-")
            for value in relationship_trace.authority_ids
        )

def test_final_review_external_validator_projection_allows_unknown_version():
    service = object.__new__(FinalModelReviewReadService)

    evidence = service._external_validator_evidence(
        {
            "external_validator_evidence": [
                {
                    "validator_identity": {
                        "tool_name": "SYSIDE Modeler CLI",
                        "tool_version": None,
                    },
                    "execution_status": "completed",
                    "exit_code": 0,
                    "normalized_diagnostic_count": 0,
                }
            ]
        }
    )

    assert len(evidence) == 1
    assert evidence[0].tool_name == "SYSIDE Modeler CLI"
    assert evidence[0].tool_version is None
    assert evidence[0].execution_status == "completed"
    assert evidence[0].exit_code == 0
    assert evidence[0].normalized_diagnostic_count == 0
