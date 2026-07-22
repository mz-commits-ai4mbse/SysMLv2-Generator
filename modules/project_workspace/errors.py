"""Exceptions raised by Project Workspace operations."""


class ProjectWorkspaceError(Exception):
    """Base exception for all Project Workspace failures."""


class ProjectManifestError(ProjectWorkspaceError):
    """Raised when a project manifest violates its contract."""


class ProjectNotFoundError(ProjectWorkspaceError):
    """Raised when a requested project does not exist."""


class DuplicateProjectNameError(ProjectWorkspaceError):
    """Raised when a normalized project display name already exists."""


class ProjectIdGenerationError(ProjectWorkspaceError):
    """Raised when no available project identifier can be generated."""


class UnsafeProjectPathError(ProjectWorkspaceError):
    """Raised when a project path violates workspace isolation rules."""