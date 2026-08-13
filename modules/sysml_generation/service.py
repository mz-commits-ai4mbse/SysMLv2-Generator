"""Phase-J orchestration boundary from explicit IEM identity to generated artifact set."""

from __future__ import annotations

from pathlib import Path

from modules.internal_model.phase_j_read_service import InternalModelReadService
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .artifact_builder import SysMLArtifactSetBuilder
from .types import GeneratedSysMLArtifactSet


class SysMLGenerationService:
    """Generate one immutable SysML artifact set from one explicitly selected IEM."""

    def __init__(
        self,
        *,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        read_service: InternalModelReadService | None = None,
        artifact_builder: SysMLArtifactSetBuilder | None = None,
    ) -> None:
        self._read_service = (
            InternalModelReadService(root=root)
            if read_service is None
            else read_service
        )
        self._artifact_builder = (
            SysMLArtifactSetBuilder()
            if artifact_builder is None
            else artifact_builder
        )

    def generate(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ) -> GeneratedSysMLArtifactSet:
        """Generate exactly one Phase-K-ready artifact set from explicit IEM identity."""

        snapshot = self._read_service.load_phase_j_input(
            project_id,
            internal_engineering_model_id,
        )
        return self._artifact_builder.build(snapshot)
