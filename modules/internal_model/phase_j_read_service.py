"""Explicit validated Phase-I → Phase-J Internal Model read boundary."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .errors import InternalModelIntegrityError
from .repository import InternalModelRepository
from .repository_integrity import (
    validate_internal_engineering_model_snapshot,
)
from .types import InternalEngineeringModelSnapshot


class InternalModelReadService:
    """Expose one explicitly addressed validated IEM snapshot to Phase J."""

    def __init__(
        self,
        *,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        repository: InternalModelRepository | None = None,
    ) -> None:
        self._repository = (
            InternalModelRepository(root=root)
            if repository is None
            else repository
        )

    def load_phase_j_input(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ) -> InternalEngineeringModelSnapshot:
        """Load exactly one immutable IEM snapshot for SysML-v2 generation."""

        scan = self._repository.scan_project(project_id)
        if scan.issues:
            first = scan.issues[0]
            raise InternalModelIntegrityError(
                "Phase-J input is blocked by Internal Model repository "
                f"integrity issue {first.code}: {first.message}"
            )

        snapshot = self._repository.load_snapshot(
            project_id,
            internal_engineering_model_id,
        )
        return validate_internal_engineering_model_snapshot(snapshot)
