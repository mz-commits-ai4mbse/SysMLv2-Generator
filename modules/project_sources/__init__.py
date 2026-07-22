"""Public API for persistent project source registration."""

from .errors import (
    DuplicateSourceContentError,
    ProjectSourceError,
    SourceIdExhaustedError,
    SourceIntegrityError,
    SourceManifestError,
    SourceNotFoundError,
    UnsupportedSourceRoleError,
    UnsafeSourcePathError,
)
from .manifest import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    SOURCE_ROLES,
)
from .registry import ProjectSourceRegistry
from .types import (
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)

__all__ = [
    "CONTEXT_ONLY_SOURCE_ROLE",
    "DuplicateSourceContentError",
    "ENGINEERING_SOURCE_ROLE",
    "ProjectSourceError",
    "ProjectSourceRegistry",
    "SOURCE_ROLES",
    "SourceIdExhaustedError",
    "SourceIntegrityError",
    "SourceIssue",
    "SourceManifest",
    "SourceManifestError",
    "SourceNotFoundError",
    "SourceScanResult",
    "UnsupportedSourceRoleError",
    "UnsafeSourcePathError",
]
