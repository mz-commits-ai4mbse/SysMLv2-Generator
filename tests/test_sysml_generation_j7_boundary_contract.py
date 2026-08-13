from __future__ import annotations

from modules.internal_model.phase_j_read_service import InternalModelReadService
from modules.sysml_generation import (
    GeneratedSysMLArtifactSet,
    SysMLArtifactSetBuilder,
    SysMLGenerationService,
)


def test_phase_j_public_boundary_contract_is_complete() -> None:
    assert callable(InternalModelReadService.load_phase_j_input)
    assert callable(SysMLGenerationService.generate)
    assert callable(SysMLArtifactSetBuilder.build)
    assert GeneratedSysMLArtifactSet.__dataclass_params__.frozen is True


def test_phase_j_result_annotation_is_generated_artifact_set() -> None:
    annotations = SysMLGenerationService.generate.__annotations__
    assert annotations["return"] in {
        "GeneratedSysMLArtifactSet",
        GeneratedSysMLArtifactSet,
    }
