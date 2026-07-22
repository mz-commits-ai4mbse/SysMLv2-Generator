"""Public API for persistent project workspaces."""

from .errors import (
    DuplicateProjectNameError,
    ProjectIdGenerationError,
    ProjectManifestError,
    ProjectNotFoundError,
    ProjectWorkspaceError,
    UnsafeProjectPathError,
)
from .types import (
    FrameworkTemplateReference,
    ProjectManifest,
    WorkspaceIssue,
    WorkspaceScanResult,
)
from .workspace import ProjectWorkspace

__all__ = [
    "DuplicateProjectNameError",
    "FrameworkTemplateReference",
    "ProjectIdGenerationError",
    "ProjectManifest",
    "ProjectManifestError",
    "ProjectNotFoundError",
    "ProjectWorkspace",
    "ProjectWorkspaceError",
    "UnsafeProjectPathError",
    "WorkspaceIssue",
    "WorkspaceScanResult",
]