"""Public API for project-bound ingestion integration."""

from .errors import (
    ProjectIngestionError,
    ProjectIngestionInputError,
    ProjectIngestionTemporaryFileError,
)
from .service import ProjectBoundIngestionService
from .types import (
    ProjectBoundSourceInventory,
    ProjectBoundSourceIssue,
    ProjectBoundSourceSummary,
)

__all__ = [
    "ProjectBoundIngestionService",
    "ProjectBoundSourceInventory",
    "ProjectBoundSourceIssue",
    "ProjectBoundSourceSummary",
    "ProjectIngestionError",
    "ProjectIngestionInputError",
    "ProjectIngestionTemporaryFileError",
]
