"""External-validator boundary for Phase-K compatibility checking."""

from __future__ import annotations

from typing import Protocol

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .types import SysMLExternalValidationRun


class SysMLExternalValidator(Protocol):
    """Protocol implemented by controlled external SysML validators."""

    def validate(
        self,
        artifact_set: GeneratedSysMLArtifactSet,
    ) -> SysMLExternalValidationRun:
        """Validate one immutable generated artifact without mutating it."""
        ...
