"""Immutable diagnostic types for Internal Model persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .types import InternalEngineeringModelSnapshot


@dataclass(frozen=True, slots=True)
class InternalModelRepositoryIssue:
    """One deterministic blocking issue discovered during repository scan."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None
    internal_engineering_model_id: str | None = None
    internal_model_element_id: str | None = None
    internal_model_relationship_id: str | None = None


@dataclass(frozen=True, slots=True)
class InternalModelRepositoryScanResult:
    """Validated IEM snapshots plus explicit blocking repository issues."""

    snapshots: tuple[InternalEngineeringModelSnapshot, ...] = ()
    issues: tuple[InternalModelRepositoryIssue, ...] = ()
