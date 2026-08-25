"""Immutable persistence for Model Assembly Drafts."""

from __future__ import annotations

from pathlib import Path

from modules.model_assembly.builder import (
    model_assembly_draft_from_json,
    model_assembly_draft_to_json,
)
from modules.model_placement.errors import ModelPlacementContractError


class ModelAssemblyRepository:
    def __init__(self, root=Path("data/projects")):
        self.root = Path(root)

    def persist(self, draft):
        directory = (
            self.root
            / draft.project_id
            / "model_assemblies"
            / draft.comparison_fingerprint
        )
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "assembly_draft.json"
        if path.exists():
            loaded = self.load(
                draft.project_id,
                draft.comparison_fingerprint,
            )
            if loaded != draft:
                raise ModelPlacementContractError(
                    "Existing Model Assembly Draft differs from requested content."
                )
            return loaded
        path.write_text(
            model_assembly_draft_to_json(draft),
            encoding="utf-8",
        )
        return self.load(
            draft.project_id,
            draft.comparison_fingerprint,
        )

    def load_if_available(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return one persisted Assembly Draft when present, else None."""

        path = (
            self.root
            / project_id
            / "model_assemblies"
            / comparison_fingerprint
            / "assembly_draft.json"
        )
        if path.is_symlink():
            raise ModelPlacementContractError(
                "Model Assembly Draft must not be a symbolic link."
            )
        if not path.exists():
            return None
        return self.load(project_id, comparison_fingerprint)

    def load(self, project_id: str, comparison_fingerprint: str):
        path = (
            self.root
            / project_id
            / "model_assemblies"
            / comparison_fingerprint
            / "assembly_draft.json"
        )
        if path.is_symlink():
            raise ModelPlacementContractError(
                "Model Assembly Draft must not be a symbolic link."
            )
        if not path.is_file():
            raise ModelPlacementContractError(
                "Model Assembly Draft not found."
            )
        value = model_assembly_draft_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.comparison_fingerprint != comparison_fingerprint
        ):
            raise ModelPlacementContractError(
                "Model Assembly Draft binding is invalid."
            )
        return value
