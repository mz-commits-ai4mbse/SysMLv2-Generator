"""Immutable I2A persistence types for ADR-032 project reconciliation."""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_engineering_authority.types import (
    ProjectAuthoritySubjectBinding,
)


PROJECT_RECONCILIATION_CYCLE_SCHEMA_VERSION = "1.0.0"
PROJECT_AUTHORITY_BINDING_SNAPSHOT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ProjectReconciliationCycleManifest:
    """Immutable anchor for one exact cross-source reconciliation cycle."""

    schema_version: str
    project_id: str
    reconciliation_cycle_id: str
    source_ids: tuple[str, ...]
    project_fit_fingerprints: tuple[str, ...]
    semantic_reconciliation_fingerprint: str
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityBindingSnapshot:
    """Frozen S3 -> source-local reviewed-authority bridge for Human S4 review."""

    schema_version: str
    project_id: str
    reconciliation_fingerprint: str
    bindings: tuple[ProjectAuthoritySubjectBinding, ...]
    content_fingerprint: str
