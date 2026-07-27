"""Exceptions raised by project-bound ingestion integration."""


class ProjectIngestionError(Exception):
    """Base exception for project-bound ingestion integration failures."""


class ProjectIngestionInputError(ProjectIngestionError):
    """Raised when uploaded input is missing or unsafe."""


class ProjectIngestionTemporaryFileError(ProjectIngestionError):
    """Raised when temporary upload material cannot be prepared."""
