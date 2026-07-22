"""Exceptions raised by the Project Source Registry."""


class ProjectSourceError(Exception):
    """Base exception for Project Source Registry failures."""


class SourceManifestError(ProjectSourceError):
    """Raised when a Source Manifest is invalid."""


class SourceNotFoundError(ProjectSourceError):
    """Raised when a requested source does not exist."""


class DuplicateSourceContentError(ProjectSourceError):
    """Raised when identical source content already exists in a project."""


class SourceIdExhaustedError(ProjectSourceError):
    """Raised when no further project-local Source ID can be allocated."""


class UnsupportedSourceRoleError(SourceManifestError):
    """Raised when a source role is not permitted."""


class UnsafeSourcePathError(ProjectSourceError):
    """Raised when a source path violates the storage safety boundary."""


class SourceIntegrityError(ProjectSourceError):
    """Raised when stored source content does not match its manifest."""