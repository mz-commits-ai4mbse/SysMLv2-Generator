"""Immutable data types used by the Project Workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FrameworkTemplateReference:
    """Pinned framework-template identity stored in a project manifest."""

    template_id: str
    template_version: str


@dataclass(frozen=True, slots=True)
class ProjectManifest:
    """Validated persisted metadata for one project."""

    schema_version: str
    project_id: str
    display_name: str
    description: str
    framework_template: FrameworkTemplateReference
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class WorkspaceIssue:
    """One validation or discovery issue found during a workspace scan."""

    code: str
    message: str
    path: Path
    project_id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceScanResult:
    """Valid projects and explicit issues returned by a workspace scan."""

    valid_projects: tuple[ProjectManifest, ...]
    workspace_issues: tuple[WorkspaceIssue, ...]