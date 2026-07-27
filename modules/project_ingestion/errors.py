"""Exceptions raised by project-bound ingestion integration."""


class ProjectIngestionError(Exception):
    """Base exception for project-bound ingestion integration failures."""


class ProjectIngestionInputError(ProjectIngestionError):
    """Raised when uploaded input is missing or unsafe."""


class ProjectIngestionTemporaryFileError(ProjectIngestionError):
    """Raised when temporary upload material cannot be prepared."""


class ProjectIngestionConfigurationError(ProjectIngestionError):
    """Raised when material execution configuration is invalid."""


class ProjectIngestionExecutionError(ProjectIngestionError):
    """Raised when a Processing Run cannot be executed safely."""


class ProjectIngestionPathError(ProjectIngestionError):
    """Raised when a project-bound execution path is unsafe."""


class ProjectIngestionOutputValidationError(ProjectIngestionError):
    """Raised before publication when required work output is invalid."""


class ProjectIngestionPublicationError(ProjectIngestionError):
    """Raised when validated output cannot begin publication."""


class ProjectIngestionRecoveryRequiredError(ProjectIngestionError):
    """Raised after publication creates partial final state."""
